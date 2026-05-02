"""
EmuFlow API — Devices Router.

Persistent device telemetry endpoints. Replaces the previous in-memory
dictionary with a SQLAlchemy-backed implementation.

Endpoints
---------
- ``POST /devices/heartbeat``                 — anonymous upsert + emulator
                                                inventory + heartbeat event.
- ``POST /devices/crash-events``              — ingest a crash event from agent.
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
from pydantic import BaseModel, ConfigDict, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.hardware.profiler import HardwareProfiler
from database import get_session
from models import CrashEvent, Device, DeviceEvent, EventType, InstalledEmulator

logger = logging.getLogger(__name__)

router = APIRouter()
profiler = HardwareProfiler()

# Per-IP rate limiter — shared across the app via main.py.
limiter = Limiter(key_func=get_remote_address)

ONLINE_WINDOW = timedelta(minutes=5)
MIN_AGENT_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# In-memory caches for ROM-library and launcher reports.
#
# Phase-1 design choice (blueprint 17 + 18):
# The agent ships **aggregated counts only** — no titles, paths or hashes.
# Because the data is pure summary state (always overwritten by the next
# heartbeat) we cache it in-process keyed by ``device_id`` rather than
# adding new SQL tables / migrations. On Railway restart the cache is empty
# and gets repopulated by the next agent report.
# ---------------------------------------------------------------------------
_library_reports: dict[str, dict] = {}
_launcher_reports: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Pydantic models (v2)
# ---------------------------------------------------------------------------


class InstalledEmulatorIn(BaseModel):
    package_name: str = Field(..., min_length=1, max_length=255)
    version: Optional[str] = Field(None, max_length=64)
    install_method: Optional[str] = Field(None, max_length=32)


class SaveEvents24h(BaseModel):
    """Aggregated save-event statistics for the last 24-hour window."""

    saves_total: int = Field(0, ge=0)
    saves_per_emulator: dict[str, int] = Field(default_factory=dict)
    vault_size_mb: int = Field(0, ge=0)
    vault_versions_total: int = Field(0, ge=0)
    backup_failures_24h: int = Field(0, ge=0)


class HeartbeatRequest(BaseModel):
    """Payload posted by the on-device agent on a regular cadence.

    All Phase-1 OS/hardware fields are optional so existing agents remain
    fully backwards-compatible. ``is_rooted`` defaults to False when absent.
    """

    model_config = ConfigDict(extra="ignore")

    # --- Existing required fields ---
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

    # --- Phase 1: OS / device identity ---
    manufacturer: Optional[str] = Field(None, max_length=128)
    model: Optional[str] = Field(None, max_length=128)
    android_release: Optional[str] = Field(None, max_length=32)

    # --- Phase 1: SoC / GPU ---
    soc_vendor: Optional[str] = Field(None, max_length=128)
    soc_chip: Optional[str] = Field(None, max_length=128)
    gpu_family: Optional[str] = Field(None, max_length=128)

    # --- Phase 1: Memory ---
    page_size: Optional[int] = Field(None, ge=0)
    ram_mb: Optional[int] = Field(None, ge=0)

    # --- Phase 1: Shizuku + root ---
    shizuku_version: Optional[int] = Field(None, ge=0)
    is_rooted: bool = False

    # --- Phase 1: Controller profile ---
    has_analog_sticks: Optional[bool] = None
    controller_layout: Optional[str] = Field(None, max_length=32)

    # --- Phase 1: Vendor packages (no ROM filenames — DSA art. 6 safe) ---
    vendor_shell_packages: Optional[list[str]] = None

    # --- Phase 1: Thermal / battery ---
    thermal_state: Optional[str] = Field(None, max_length=32)
    battery_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    battery_temperature_c: Optional[float] = Field(None, ge=-20.0, le=100.0)

    # --- Phase 1: Save-event aggregates (last 24 h) ---
    save_events_24h: Optional[SaveEvents24h] = None

    @field_validator("controller_layout")
    @classmethod
    def _validate_layout(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"dual_stick", "no_stick", "single_stick"}
        if v not in allowed:
            raise ValueError(f"controller_layout must be one of {sorted(allowed)}")
        return v


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

    # Phase 1 additions
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    android_release: Optional[str] = None
    soc_vendor: Optional[str] = None
    soc_chip: Optional[str] = None
    gpu_family: Optional[str] = None
    page_size: Optional[int] = None
    ram_mb: Optional[int] = None
    shizuku_version: Optional[int] = None
    is_rooted: bool = False
    has_analog_sticks: Optional[bool] = None
    controller_layout: Optional[str] = None
    vendor_shell_packages: Optional[list] = None
    thermal_state: Optional[str] = None
    battery_level: Optional[float] = None
    battery_temperature_c: Optional[float] = None
    last_heartbeat_at: Optional[datetime] = None
    save_events_24h: Optional[dict] = None


class DeviceDetail(DeviceListItem):
    created_at: datetime
    updated_at: datetime
    hardware_fingerprint: str
    recent_events: list[DeviceEventOut]
    installed_emulators: list[InstalledEmulatorOut]


# ---------------------------------------------------------------------------
# Crash-event models
# ---------------------------------------------------------------------------


class CrashEventRequest(BaseModel):
    """Crash telemetry posted by the on-device agent.

    ``game_id`` must be an official product code (e.g. SLUS-00123).
    ROM filenames and hashes are explicitly forbidden (DSA art. 6 compliance).
    """

    model_config = ConfigDict(extra="ignore")

    hardware_fingerprint: str = Field(..., min_length=8, max_length=128)
    timestamp: datetime

    emulator_package: Optional[str] = Field(None, max_length=255)
    emulator_version_name: Optional[str] = Field(None, max_length=64)
    emulator_version_code: Optional[int] = Field(None, ge=0)

    # Official product code only — NOT a filename or hash
    game_id: Optional[str] = Field(None, max_length=64)
    platform: Optional[str] = Field(None, max_length=32)
    duration_played_sec: Optional[int] = Field(None, ge=0)

    crash_reason: Optional[str] = Field(None, max_length=255)
    crash_signal: Optional[str] = Field(None, max_length=32)

    rss_mb: Optional[int] = Field(None, ge=0)
    pss_mb: Optional[int] = Field(None, ge=0)

    stacktrace_hash: Optional[str] = Field(None, max_length=64)
    tombstone_excerpt: Optional[str] = Field(None, max_length=4096)

    thermal_state: Optional[str] = Field(None, max_length=32)
    battery_level: Optional[float] = Field(None, ge=0.0, le=100.0)
    battery_temperature_c: Optional[float] = Field(None, ge=-20.0, le=100.0)
    free_ram_mb: Optional[int] = Field(None, ge=0)
    page_size: Optional[int] = Field(None, ge=0)


class CrashEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    timestamp: datetime
    emulator_package: Optional[str]
    game_id: Optional[str]
    platform: Optional[str]
    crash_reason: Optional[str]
    crash_signal: Optional[str]
    created_at: datetime


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


def _device_to_list_item(d: Device, now: datetime) -> DeviceListItem:
    return DeviceListItem(
        device_id=d.id,
        device_name=d.device_name,
        chipset=d.chipset,
        android_api=d.android_api,
        ram_gb=d.ram_gb,
        shizuku_available=d.shizuku_available,
        agent_version=d.agent_version,
        last_seen=d.last_seen,
        online=_is_online(d.last_seen, now),
        manufacturer=d.manufacturer,
        model=d.model,
        android_release=d.android_release,
        soc_vendor=d.soc_vendor,
        soc_chip=d.soc_chip,
        gpu_family=d.gpu_family,
        page_size=d.page_size,
        ram_mb=d.ram_mb,
        shizuku_version=d.shizuku_version,
        is_rooted=d.is_rooted,
        has_analog_sticks=d.has_analog_sticks,
        controller_layout=d.controller_layout,
        vendor_shell_packages=d.vendor_shell_packages,
        thermal_state=d.thermal_state,
        battery_level=d.battery_level,
        battery_temperature_c=d.battery_temperature_c,
        last_heartbeat_at=d.last_heartbeat_at,
        save_events_24h=d.save_events_24h,
    )


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
    - All Phase-1 fields are optional — old agents without them remain compatible.
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

    # Capture client IP for admin-only last_known_ip field.
    client_ip: str | None = None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host

    result = await session.execute(
        select(Device).where(Device.hardware_fingerprint == payload.hardware_fingerprint)
    )
    device = result.scalar_one_or_none()

    # Common field updates applied to both new and existing devices.
    def _apply_payload(dev: Device) -> None:
        dev.device_name = payload.device_name
        dev.chipset = payload.chipset
        dev.android_api = payload.android_api
        dev.ram_gb = payload.ram_gb
        dev.shizuku_available = payload.shizuku_available
        dev.agent_version = effective_version
        dev.last_seen = now
        dev.last_heartbeat_at = now
        if client_ip:
            dev.last_known_ip = client_ip

        # Phase 1 optional fields — only overwrite if provided
        if payload.manufacturer is not None:
            dev.manufacturer = payload.manufacturer
        if payload.model is not None:
            dev.model = payload.model
        if payload.android_release is not None:
            dev.android_release = payload.android_release
        if payload.soc_vendor is not None:
            dev.soc_vendor = payload.soc_vendor
        if payload.soc_chip is not None:
            dev.soc_chip = payload.soc_chip
        if payload.gpu_family is not None:
            dev.gpu_family = payload.gpu_family
        if payload.page_size is not None:
            dev.page_size = payload.page_size
        if payload.ram_mb is not None:
            dev.ram_mb = payload.ram_mb
        if payload.shizuku_version is not None:
            dev.shizuku_version = payload.shizuku_version
        dev.is_rooted = payload.is_rooted
        if payload.has_analog_sticks is not None:
            dev.has_analog_sticks = payload.has_analog_sticks
        if payload.controller_layout is not None:
            dev.controller_layout = payload.controller_layout
        if payload.vendor_shell_packages is not None:
            dev.vendor_shell_packages = payload.vendor_shell_packages
        if payload.thermal_state is not None:
            dev.thermal_state = payload.thermal_state
        if payload.battery_level is not None:
            dev.battery_level = payload.battery_level
        if payload.battery_temperature_c is not None:
            dev.battery_temperature_c = payload.battery_temperature_c
        if payload.save_events_24h is not None:
            dev.save_events_24h = payload.save_events_24h.model_dump()

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
        _apply_payload(device)
        logger.info("New device registered: id=%s name=%s", device.id, device.device_name)
    else:
        _apply_payload(device)

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

    # Heartbeat event — no ROM data, DSA-safe payload.
    event_payload = {
        "battery_pct": payload.battery_pct,
        "storage_free_gb": payload.storage_free_gb,
        "agent_version": effective_version,
        "ram_gb": payload.ram_gb,
        "shizuku_available": payload.shizuku_available,
        # Phase 1 additions
        "thermal_state": payload.thermal_state,
        "battery_level": payload.battery_level,
        "battery_temperature_c": payload.battery_temperature_c,
        "soc_vendor": payload.soc_vendor,
        "soc_chip": payload.soc_chip,
        "is_rooted": payload.is_rooted,
        "controller_layout": payload.controller_layout,
        "has_analog_sticks": payload.has_analog_sticks,
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
    "/crash-events",
    response_model=CrashEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a crash event from the on-device agent.",
)
@limiter.limit("120/minute")
async def post_crash_event(
    request: Request,
    payload: CrashEventRequest,
    session: SessionDep,
) -> CrashEventResponse:
    """Accept a crash telemetry event from a known device.

    Resolves the device by ``hardware_fingerprint``. Returns 404 if the
    device has not heartbeated yet (agent should call heartbeat first).

    No ROM filenames or hashes are accepted in this endpoint.
    ``game_id`` must be an official product code (DSA art. 6 compliant).
    """
    result = await session.execute(
        select(Device).where(Device.hardware_fingerprint == payload.hardware_fingerprint)
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No device found for fingerprint "
                f"'{payload.hardware_fingerprint[:12]}…'. "
                "Call POST /devices/heartbeat first."
            ),
        )

    crash = CrashEvent(
        device_id=device.id,
        timestamp=payload.timestamp,
        emulator_package=payload.emulator_package,
        emulator_version_name=payload.emulator_version_name,
        emulator_version_code=payload.emulator_version_code,
        game_id=payload.game_id,
        platform=payload.platform,
        duration_played_sec=payload.duration_played_sec,
        crash_reason=payload.crash_reason,
        crash_signal=payload.crash_signal,
        rss_mb=payload.rss_mb,
        pss_mb=payload.pss_mb,
        stacktrace_hash=payload.stacktrace_hash,
        tombstone_excerpt=payload.tombstone_excerpt,
        thermal_state=payload.thermal_state,
        battery_level=payload.battery_level,
        battery_temperature_c=payload.battery_temperature_c,
        free_ram_mb=payload.free_ram_mb,
        page_size=payload.page_size,
    )
    session.add(crash)
    await session.commit()
    await session.refresh(crash)

    logger.info(
        "Crash event recorded: device=%s emulator=%s game=%s",
        device.id,
        crash.emulator_package,
        crash.game_id,
    )
    return CrashEventResponse.model_validate(crash)


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
    return [_device_to_list_item(d, now) for d in devices]


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

    now = datetime.now(timezone.utc)
    base = _device_to_list_item(device, now)

    return DeviceDetail(
        **base.model_dump(),
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


# ---------------------------------------------------------------------------
# ROM-library + launcher endpoints (Blueprint 17 + 18)
#
# These endpoints carry **aggregated, anonymous counts** only. ROM titles,
# paths and SHA1 hashes are not transmitted — they remain in the agent's
# private SQLite index. This satisfies blueprint 17's privacy constraint and
# DSA art. 6.
# ---------------------------------------------------------------------------


class LibraryStatsRequest(BaseModel):
    """Aggregated ROM-library stats posted by the on-device agent."""

    model_config = ConfigDict(extra="ignore")

    hardware_fingerprint: str = Field(..., min_length=8, max_length=128)
    total_count: int = Field(0, ge=0)
    by_platform: dict[str, int] = Field(default_factory=dict)
    preinstalled_count: int = Field(0, ge=0)
    duplicate_groups_exact: int = Field(0, ge=0)
    duplicate_groups_probable: int = Field(0, ge=0)
    language_candidates: int = Field(0, ge=0)
    scan_completed_at: Optional[datetime] = None


class LibraryStatsResponse(BaseModel):
    device_id: str
    total_count: int
    by_platform: dict[str, int]
    preinstalled_count: int
    duplicate_groups_exact: int
    duplicate_groups_probable: int
    language_candidates: int
    scan_completed_at: Optional[datetime]
    reported_at: datetime


class LauncherInfo(BaseModel):
    """Single detected launcher entry."""

    model_config = ConfigDict(extra="ignore")

    package_name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    is_default_home: bool = False
    is_installed: bool = True
    boxart_capability: str = Field("none", max_length=32)  # auto | manual | none
    video_capability: str = Field("none", max_length=32)   # auto | manual | none
    notes: Optional[str] = Field(None, max_length=512)


class LauncherReportRequest(BaseModel):
    """Aggregated launcher-detection report from the on-device agent."""

    model_config = ConfigDict(extra="ignore")

    hardware_fingerprint: str = Field(..., min_length=8, max_length=128)
    detected: list[LauncherInfo] = Field(default_factory=list)
    active_home_package: Optional[str] = Field(None, max_length=255)
    detected_at: Optional[datetime] = None


class LauncherReportResponse(BaseModel):
    device_id: str
    detected: list[LauncherInfo]
    active_home_package: Optional[str]
    detected_at: Optional[datetime]
    reported_at: datetime


async def _resolve_device_by_fingerprint(
    session: AsyncSession, fingerprint: str
) -> Device:
    result = await session.execute(
        select(Device).where(Device.hardware_fingerprint == fingerprint)
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No device for fingerprint '{fingerprint[:12]}…'. "
                "Call POST /devices/heartbeat first."
            ),
        )
    return device


@router.post(
    "/library/scan-results",
    response_model=LibraryStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent posts aggregated ROM-library scan results.",
)
@limiter.limit("30/minute")
async def post_library_scan(
    request: Request,
    payload: LibraryStatsRequest,
    session: SessionDep,
) -> LibraryStatsResponse:
    """Receive aggregated ROM-library counters from the on-device agent.

    The payload contains **counts only** — no game titles, paths or hashes.
    Stored in-memory keyed by ``device_id`` (overwritten on each report).
    """
    device = await _resolve_device_by_fingerprint(
        session, payload.hardware_fingerprint
    )
    now = datetime.now(timezone.utc)
    record = {
        "device_id": device.id,
        "total_count": payload.total_count,
        "by_platform": dict(payload.by_platform),
        "preinstalled_count": payload.preinstalled_count,
        "duplicate_groups_exact": payload.duplicate_groups_exact,
        "duplicate_groups_probable": payload.duplicate_groups_probable,
        "language_candidates": payload.language_candidates,
        "scan_completed_at": payload.scan_completed_at,
        "reported_at": now,
    }
    _library_reports[device.id] = record
    logger.info(
        "Library scan stored: device=%s total=%d preinstalled=%d dup_exact=%d",
        device.id,
        payload.total_count,
        payload.preinstalled_count,
        payload.duplicate_groups_exact,
    )
    return LibraryStatsResponse(**record)


@router.get(
    "/{device_id}/library",
    response_model=LibraryStatsResponse,
    summary="Latest aggregated ROM-library stats for a device.",
)
async def get_device_library(
    device_id: str, session: SessionDep
) -> LibraryStatsResponse:
    """Return the most recent ROM-library report posted by the agent.

    Returns 404 with a friendly hint if the agent hasn't reported yet.
    """
    # Verify the device exists first (better error than 'no library data').
    result = await session.execute(select(Device).where(Device.id == device_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown device '{device_id}'.",
        )
    record = _library_reports.get(device_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No ROM-library report for this device yet. "
                "The agent will post it after the first scan."
            ),
        )
    return LibraryStatsResponse(**record)


@router.post(
    "/launchers/report",
    response_model=LauncherReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent posts detected launcher inventory.",
)
@limiter.limit("30/minute")
async def post_launcher_report(
    request: Request,
    payload: LauncherReportRequest,
    session: SessionDep,
) -> LauncherReportResponse:
    """Receive the agent's launcher-detection report.

    Each entry includes capability flags so the frontend /media page knows
    whether boxart / gameplay video can be auto-fetched, requires manual
    setup, or is unsupported per launcher.
    """
    device = await _resolve_device_by_fingerprint(
        session, payload.hardware_fingerprint
    )
    now = datetime.now(timezone.utc)
    record = {
        "device_id": device.id,
        "detected": [info.model_dump() for info in payload.detected],
        "active_home_package": payload.active_home_package,
        "detected_at": payload.detected_at,
        "reported_at": now,
    }
    _launcher_reports[device.id] = record
    logger.info(
        "Launcher report stored: device=%s count=%d home=%s",
        device.id,
        len(payload.detected),
        payload.active_home_package,
    )
    # Re-hydrate for response (model_validate works on plain dicts too).
    return LauncherReportResponse(
        device_id=device.id,
        detected=payload.detected,
        active_home_package=payload.active_home_package,
        detected_at=payload.detected_at,
        reported_at=now,
    )


@router.get(
    "/{device_id}/launchers",
    response_model=LauncherReportResponse,
    summary="Latest launcher-detection report for a device.",
)
async def get_device_launchers(
    device_id: str, session: SessionDep
) -> LauncherReportResponse:
    """Return the most recent launcher-detection report from the agent."""
    result = await session.execute(select(Device).where(Device.id == device_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown device '{device_id}'.",
        )
    record = _launcher_reports.get(device_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No launcher report for this device yet. "
                "The agent will post it after first launcher scan."
            ),
        )
    return LauncherReportResponse(
        device_id=record["device_id"],
        detected=[LauncherInfo(**i) for i in record["detected"]],
        active_home_package=record["active_home_package"],
        detected_at=record["detected_at"],
        reported_at=record["reported_at"],
    )
