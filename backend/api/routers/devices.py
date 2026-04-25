"""
EmuFlow API — Devices Router.

Persistent device telemetry endpoints. Replaces the previous in-memory
dictionary with a SQLAlchemy-backed implementation.

Endpoints
---------
- ``POST /devices/heartbeat``                 — anonymous upsert + emulator
                                                inventory + heartbeat event.
- ``POST /devices/{device_id}/events``        — log an arbitrary event.
- ``GET  /devices``                           — list devices with online flag.
- ``GET  /devices/{device_id}``               — detail + recent events +
                                                installed emulators.
- ``GET  /devices/{device_id}/events``        — paginated event history with
                                                optional ``type`` filter.
- ``GET  /devices/{device_id}/profile``       — hardware-tier recommendations.
- ``POST /devices/register``                  — **deprecated** legacy
                                                register endpoint kept for
                                                backwards compatibility.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.hardware.profiler import HardwareProfiler
from database import get_session
from models import Device, DeviceEvent, EventType, InstalledEmulator

logger = logging.getLogger(__name__)

router = APIRouter()
profiler = HardwareProfiler()

# Per-IP rate limiter — shared across the app via main.py.
limiter = Limiter(key_func=get_remote_address)

ONLINE_WINDOW = timedelta(minutes=5)
MIN_AGENT_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Pydantic models (v2)
# ---------------------------------------------------------------------------


class InstalledEmulatorIn(BaseModel):
    package_name: str = Field(..., min_length=1, max_length=255)
    version: Optional[str] = Field(None, max_length=64)
    install_method: Optional[str] = Field(None, max_length=32)


class HeartbeatRequest(BaseModel):
    """Payload posted by the on-device agent on a regular cadence."""

    model_config = ConfigDict(extra="ignore")

    hardware_fingerprint: str = Field(..., min_length=8, max_length=128)
    device_name: str = Field(..., min_length=1, max_length=255)
    chipset: str = Field(..., min_length=1, max_length=255)
    android_api: int = Field(..., ge=21, le=99)
    ram_gb: float = Field(..., gt=0, le=1024)
    shizuku_available: bool = False
    agent_version: Optional[str] = Field(None, max_length=32)
    battery_pct: Optional[int] = Field(None, ge=0, le=100)
    storage_free_gb: Optional[float] = Field(None, ge=0)
    installed_emulators: list[InstalledEmulatorIn] = Field(default_factory=list)


class HeartbeatResponse(BaseModel):
    device_id: str
    server_time: datetime
    online: bool = True


class DeviceEventIn(BaseModel):
    event_type: EventType
    payload: dict = Field(default_factory=dict)


class DeviceEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: EventType
    payload: dict
    created_at: datetime


class InstalledEmulatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    package_name: str
    version: Optional[str]
    install_method: Optional[str]
    installed_at: datetime


class DeviceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    device_name: str
    chipset: str
    android_api: int
    ram_gb: float
    shizuku_available: bool
    agent_version: Optional[str]
    last_seen: datetime
    online: bool


class DeviceDetail(DeviceListItem):
    created_at: datetime
    updated_at: datetime
    hardware_fingerprint: str
    recent_events: list[DeviceEventOut]
    installed_emulators: list[InstalledEmulatorOut]


# Legacy compat models -------------------------------------------------------


class DeviceRegisterRequest(BaseModel):
    """Legacy register payload (deprecated, kept for backwards compat)."""

    device_name: str = Field(..., max_length=255)
    chipset: str = Field(..., max_length=255)
    android_api: int = Field(..., ge=21)
    ram_gb: float = Field(..., gt=0)
    shizuku_available: bool = False


class DeviceResponse(BaseModel):
    """Slim device response used by legacy endpoints."""

    device_id: str
    device_name: str
    chipset: str
    android_api: int
    ram_gb: float
    shizuku_available: bool
    detected_chipset_id: Optional[str] = None


class DeviceProfileResponse(BaseModel):
    device_id: str
    device_name: str
    chipset: str
    android_api: int
    ram_gb: float
    shizuku_available: bool
    chipset_id: str
    renderer: dict[str, str]
    recommended_emulators: dict[str, dict]
    performance_tier: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


def _parse_version(v: str | None) -> tuple[int, int, int] | None:
    if not v:
        return None
    m = _VERSION_RE.match(v)
    if not m:
        return None
    return tuple(int(x) for x in m.groups())  # type: ignore[return-value]


def _is_outdated(client_version: str | None, minimum: str = MIN_AGENT_VERSION) -> bool:
    cv = _parse_version(client_version)
    mv = _parse_version(minimum)
    if cv is None or mv is None:
        return False
    return cv < mv


def _is_online(last_seen: datetime, now: datetime | None = None) -> bool:
    """An agent is 'online' if it heartbeated within the online window."""
    now = now or datetime.now(timezone.utc)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    return (now - last_seen) <= ONLINE_WINDOW


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Telemetry endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent heartbeat — upsert device, log inventory + event.",
)
@limiter.limit("60/minute")
async def heartbeat(
    request: Request,
    payload: HeartbeatRequest,
    session: SessionDep,
) -> HeartbeatResponse:
    """Anonymous, rate-limited (60/min/IP) heartbeat ingestion.

    Behaviour:
    - Upsert ``Device`` keyed by ``hardware_fingerprint``.
    - Replace ``installed_emulators`` rows for that device with the inbound list.
    - Append a ``heartbeat`` ``DeviceEvent`` carrying the full payload.
    - Validate ``X-Agent-Version`` header / payload version and warn on old.
    """
    now = datetime.now(timezone.utc)

    header_version = request.headers.get("X-Agent-Version")
    effective_version = header_version or payload.agent_version
    if _is_outdated(effective_version):
        logger.warning(
            "Outdated agent heartbeat: version=%s fingerprint=%s",
            effective_version,
            payload.hardware_fingerprint[:12],
        )

    result = await session.execute(
        select(Device).where(Device.hardware_fingerprint == payload.hardware_fingerprint)
    )
    device = result.scalar_one_or_none()

    if device is None:
        device = Device(
            hardware_fingerprint=payload.hardware_fingerprint,
            device_name=payload.device_name,
            chipset=payload.chipset,
            android_api=payload.android_api,
            ram_gb=payload.ram_gb,
            shizuku_available=payload.shizuku_available,
            agent_version=effective_version,
            last_seen=now,
        )
        session.add(device)
        await session.flush()
        logger.info("New device registered: id=%s name=%s", device.id, device.device_name)
    else:
        device.device_name = payload.device_name
        device.chipset = payload.chipset
        device.android_api = payload.android_api
        device.ram_gb = payload.ram_gb
        device.shizuku_available = payload.shizuku_available
        device.agent_version = effective_version
        device.last_seen = now

    # Refresh installed emulators inventory: upsert by (device_id, package_name).
    existing_q = await session.execute(
        select(InstalledEmulator).where(InstalledEmulator.device_id == device.id)
    )
    existing = {row.package_name: row for row in existing_q.scalars()}
    incoming = {e.package_name: e for e in payload.installed_emulators}

    for pkg, e in incoming.items():
        row = existing.get(pkg)
        if row is None:
            session.add(
                InstalledEmulator(
                    device_id=device.id,
                    package_name=pkg,
                    version=e.version,
                    install_method=e.install_method,
                    installed_at=now,
                )
            )
        else:
            row.version = e.version
            row.install_method = e.install_method
            row.installed_at = now

    for pkg, row in existing.items():
        if pkg not in incoming:
            await session.delete(row)

    # Heartbeat event with metrics payload.
    event_payload = {
        "battery_pct": payload.battery_pct,
        "storage_free_gb": payload.storage_free_gb,
        "agent_version": effective_version,
        "ram_gb": payload.ram_gb,
        "shizuku_available": payload.shizuku_available,
    }
    session.add(
        DeviceEvent(
            device_id=device.id,
            event_type=EventType.heartbeat,
            payload=event_payload,
            created_at=now,
        )
    )

    await session.commit()
    return HeartbeatResponse(device_id=device.id, server_time=now, online=True)


@router.post(
    "/{device_id}/events",
    response_model=DeviceEventOut,
    status_code=status.HTTP_201_CREATED,
    summary="Log an event for a known device.",
)
async def post_event(
    device_id: str,
    payload: DeviceEventIn,
    session: SessionDep,
) -> DeviceEventOut:
    """Append an event to a device's log."""
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    event = DeviceEvent(
        device_id=device_id,
        event_type=payload.event_type,
        payload=payload.payload,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return DeviceEventOut.model_validate(event)


@router.get(
    "",
    response_model=list[DeviceListItem],
    summary="List all devices with online status.",
)
async def list_devices(session: SessionDep) -> list[DeviceListItem]:
    """Return every registered device with its current online flag."""
    now = datetime.now(timezone.utc)
    res = await session.execute(select(Device).order_by(Device.last_seen.desc()))
    devices = res.scalars().all()
    return [
        DeviceListItem(
            device_id=d.id,
            device_name=d.device_name,
            chipset=d.chipset,
            android_api=d.android_api,
            ram_gb=d.ram_gb,
            shizuku_available=d.shizuku_available,
            agent_version=d.agent_version,
            last_seen=d.last_seen,
            online=_is_online(d.last_seen, now),
        )
        for d in devices
    ]


@router.get(
    "/{device_id}",
    response_model=DeviceDetail,
    summary="Device detail with recent events and emulators.",
)
async def get_device(device_id: str, session: SessionDep) -> DeviceDetail:
    """Return a full device record + last 50 events + installed emulators."""
    res = await session.execute(
        select(Device)
        .where(Device.id == device_id)
        .options(selectinload(Device.installed_emulators))
    )
    device = res.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    events_res = await session.execute(
        select(DeviceEvent)
        .where(DeviceEvent.device_id == device_id)
        .order_by(DeviceEvent.created_at.desc())
        .limit(50)
    )
    events = events_res.scalars().all()

    return DeviceDetail(
        device_id=device.id,
        device_name=device.device_name,
        chipset=device.chipset,
        android_api=device.android_api,
        ram_gb=device.ram_gb,
        shizuku_available=device.shizuku_available,
        agent_version=device.agent_version,
        last_seen=device.last_seen,
        online=_is_online(device.last_seen),
        created_at=device.created_at,
        updated_at=device.updated_at,
        hardware_fingerprint=device.hardware_fingerprint,
        recent_events=[DeviceEventOut.model_validate(e) for e in events],
        installed_emulators=[
            InstalledEmulatorOut.model_validate(e) for e in device.installed_emulators
        ],
    )


@router.get(
    "/{device_id}/events",
    response_model=list[DeviceEventOut],
    summary="Paginated event history with optional type filter.",
)
async def list_events(
    device_id: str,
    session: SessionDep,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    type: Optional[EventType] = Query(None, description="Filter by event_type"),
) -> list[DeviceEventOut]:
    """Return events for a device, newest first."""
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    stmt = (
        select(DeviceEvent)
        .where(DeviceEvent.device_id == device_id)
        .order_by(DeviceEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if type is not None:
        stmt = stmt.where(DeviceEvent.event_type == type)

    res = await session.execute(stmt)
    return [DeviceEventOut.model_validate(e) for e in res.scalars().all()]


# ---------------------------------------------------------------------------
# Hardware-profile recommendation (read-only, derived from chipset)
# ---------------------------------------------------------------------------


@router.get(
    "/{device_id}/profile",
    response_model=DeviceProfileResponse,
    summary="Hardware tier and per-system emulator recommendations.",
)
async def get_device_profile(device_id: str, session: SessionDep) -> DeviceProfileResponse:
    """Return performance tier + per-system renderer/emulator recommendations."""
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    detected_chipset_id = profiler.detect_chipset_from_build_info(
        {"hardware": device.chipset, "soc_model": device.chipset}
    )
    chipset_id = detected_chipset_id or "generic"

    systems = ["nes", "snes", "gba", "psp", "ps1", "ps2", "nds", "gc", "wii", "3ds", "switch"]
    recommended: dict[str, dict] = {}
    for system in systems:
        use_standalone, package = profiler.should_use_standalone(system, device.android_api)
        renderer = profiler.select_renderer(chipset_id, system)
        optimal = profiler.get_optimal_profile(chipset_id, system)
        recommended[system] = {
            "use_standalone": use_standalone,
            "package": package,
            "renderer": renderer,
            "settings": optimal,
        }

    renderer_map = {s: profiler.select_renderer(chipset_id, s) for s in systems}

    if device.ram_gb >= 12:
        tier = "high"
    elif device.ram_gb >= 6:
        tier = "mid"
    else:
        tier = "low"

    return DeviceProfileResponse(
        device_id=device.id,
        device_name=device.device_name,
        chipset=device.chipset,
        android_api=device.android_api,
        ram_gb=device.ram_gb,
        shizuku_available=device.shizuku_available,
        chipset_id=chipset_id,
        renderer=renderer_map,
        recommended_emulators=recommended,
        performance_tier=tier,
    )


# ---------------------------------------------------------------------------
# Legacy register endpoint (deprecated)
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
    summary="[Deprecated] Use POST /devices/heartbeat instead.",
)
async def register_device(
    payload: DeviceRegisterRequest, session: SessionDep
) -> DeviceResponse:
    """Backwards-compatible single-shot device registration.

    .. deprecated::
        New agents should call ``POST /devices/heartbeat`` which upserts and
        carries richer telemetry. This endpoint will be removed in a future
        release.
    """
    logger.warning("Deprecated /devices/register called (name=%s)", payload.device_name)

    # Synthesise a fingerprint from name+chipset+api so repeat calls upsert.
    import hashlib

    raw = f"{payload.device_name}|{payload.chipset}|{payload.android_api}"
    fingerprint = "legacy:" + hashlib.sha256(raw.encode()).hexdigest()

    res = await session.execute(
        select(Device).where(Device.hardware_fingerprint == fingerprint)
    )
    device = res.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if device is None:
        device = Device(
            hardware_fingerprint=fingerprint,
            device_name=payload.device_name,
            chipset=payload.chipset,
            android_api=payload.android_api,
            ram_gb=payload.ram_gb,
            shizuku_available=payload.shizuku_available,
            last_seen=now,
        )
        session.add(device)
        await session.flush()
    else:
        device.last_seen = now

    await session.commit()

    detected = profiler.detect_chipset_from_build_info(
        {"hardware": payload.chipset, "soc_model": payload.chipset}
    )
    return DeviceResponse(
        device_id=device.id,
        device_name=device.device_name,
        chipset=device.chipset,
        android_api=device.android_api,
        ram_gb=device.ram_gb,
        shizuku_available=device.shizuku_available,
        detected_chipset_id=detected,
    )
