"""
End-to-end tests for the ``/devices`` telemetry surface.

These exercise the FastAPI app in-process via ``httpx.AsyncClient`` against
an in-memory SQLite database. No network, no Postgres, no Redis required.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

import database
from models import Device

pytestmark = pytest.mark.asyncio


def _heartbeat_payload(**overrides: object) -> dict:
    base: dict[str, object] = {
        "hardware_fingerprint": "fp-" + "a" * 32,
        "device_name": "Pixel 7",
        "chipset": "Google Tensor G2",
        "android_api": 33,
        "ram_gb": 8.0,
        "shizuku_available": True,
        "agent_version": "0.2.0",
        "battery_pct": 87,
        "storage_free_gb": 64.5,
        "installed_emulators": [
            {"package_name": "org.dolphinemu.dolphinemu", "version": "5.0-21000"},
        ],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Heartbeat upsert
# ---------------------------------------------------------------------------


async def test_heartbeat_creates_new_device(client: AsyncClient) -> None:
    res = await client.post("/devices/heartbeat", json=_heartbeat_payload())
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["device_id"]
    assert body["online"] is True
    assert "server_time" in body

    async with database.SessionLocal() as s:
        rows = (await s.execute(select(Device))).scalars().all()
        assert len(rows) == 1
        assert rows[0].device_name == "Pixel 7"
        assert rows[0].agent_version == "0.2.0"


async def test_heartbeat_upsert_existing_device(client: AsyncClient) -> None:
    payload = _heartbeat_payload()
    r1 = await client.post("/devices/heartbeat", json=payload)
    assert r1.status_code == 200
    first_id = r1.json()["device_id"]

    # Same fingerprint, updated fields.
    payload2 = _heartbeat_payload(device_name="Pixel 7 (renamed)", ram_gb=12.0)
    r2 = await client.post("/devices/heartbeat", json=payload2)
    assert r2.status_code == 200
    assert r2.json()["device_id"] == first_id

    async with database.SessionLocal() as s:
        rows = (await s.execute(select(Device))).scalars().all()
        assert len(rows) == 1, "fingerprint match must not create a duplicate"
        assert rows[0].device_name == "Pixel 7 (renamed)"
        assert rows[0].ram_gb == 12.0


# ---------------------------------------------------------------------------
# Event logging + filter + paging
# ---------------------------------------------------------------------------


async def test_post_event_logs_to_database(client: AsyncClient) -> None:
    hb = await client.post("/devices/heartbeat", json=_heartbeat_payload())
    device_id = hb.json()["device_id"]

    res = await client.post(
        f"/devices/{device_id}/events",
        json={"event_type": "install_started", "payload": {"package": "org.citra"}},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["event_type"] == "install_started"
    assert body["payload"] == {"package": "org.citra"}


async def test_events_filter_by_type(client: AsyncClient) -> None:
    hb = await client.post("/devices/heartbeat", json=_heartbeat_payload())
    device_id = hb.json()["device_id"]

    for et in ("install_started", "install_done", "launch", "error", "launch"):
        await client.post(
            f"/devices/{device_id}/events",
            json={"event_type": et, "payload": {"x": et}},
        )

    res_all = await client.get(f"/devices/{device_id}/events?limit=50")
    # Heartbeat counts as an event too, so >= 6.
    assert res_all.status_code == 200
    assert len(res_all.json()) >= 6

    res_launch = await client.get(f"/devices/{device_id}/events?type=launch")
    assert res_launch.status_code == 200
    bodies = res_launch.json()
    assert len(bodies) == 2
    assert all(e["event_type"] == "launch" for e in bodies)


# ---------------------------------------------------------------------------
# List + online status
# ---------------------------------------------------------------------------


async def test_list_devices_online_flag(client: AsyncClient) -> None:
    # Fresh device — should be online.
    await client.post("/devices/heartbeat", json=_heartbeat_payload())
    # A separate device with stale last_seen.
    stale = _heartbeat_payload(
        hardware_fingerprint="fp-stale-" + "b" * 24, device_name="OldPhone"
    )
    await client.post("/devices/heartbeat", json=stale)

    async with database.SessionLocal() as s:
        res = await s.execute(select(Device).where(Device.device_name == "OldPhone"))
        old = res.scalar_one()
        old.last_seen = datetime.now(timezone.utc) - timedelta(hours=1)
        await s.commit()

    res = await client.get("/devices")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    by_name = {i["device_name"]: i for i in items}
    assert by_name["Pixel 7"]["online"] is True
    assert by_name["OldPhone"]["online"] is False


# ---------------------------------------------------------------------------
# Installed emulator inventory upsert
# ---------------------------------------------------------------------------


async def test_installed_emulators_upsert(client: AsyncClient) -> None:
    p1 = _heartbeat_payload(
        installed_emulators=[
            {"package_name": "org.dolphinemu.dolphinemu", "version": "5.0"},
            {"package_name": "org.citra.emu", "version": "1.0"},
        ]
    )
    await client.post("/devices/heartbeat", json=p1)

    p2 = _heartbeat_payload(
        installed_emulators=[
            {"package_name": "org.dolphinemu.dolphinemu", "version": "5.1"},
            {"package_name": "skyline.emu", "version": "2.0"},
        ]
    )
    r = await client.post("/devices/heartbeat", json=p2)
    device_id = r.json()["device_id"]

    detail = await client.get(f"/devices/{device_id}")
    assert detail.status_code == 200
    pkgs = {e["package_name"]: e for e in detail.json()["installed_emulators"]}
    assert set(pkgs) == {"org.dolphinemu.dolphinemu", "skyline.emu"}, (
        "removed package must be deleted, new one inserted"
    )
    assert pkgs["org.dolphinemu.dolphinemu"]["version"] == "5.1"


# ---------------------------------------------------------------------------
# Rate limit
# ---------------------------------------------------------------------------


async def test_heartbeat_rate_limit(client: AsyncClient) -> None:
    """Sending more than 60 heartbeats in a minute should yield 429."""
    payload = _heartbeat_payload()
    saw_429 = False
    for _ in range(65):
        r = await client.post("/devices/heartbeat", json=payload)
        if r.status_code == 429:
            saw_429 = True
            break
    assert saw_429, "expected at least one 429 within the burst window"


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


async def test_cors_preflight_unknown_origin_rejected(client: AsyncClient) -> None:
    """Preflight from an origin not in the allow-list must not echo it back."""
    r = await client.options(
        "/devices/heartbeat",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    # CORSMiddleware returns 400 when the origin is disallowed.
    assert r.status_code in (400, 403), r.status_code
    assert r.headers.get("access-control-allow-origin") not in (
        "https://evil.example",
        "*",
    )


async def test_legacy_register_still_works(client: AsyncClient) -> None:
    """Deprecated /register must still create+upsert a device row."""
    body = {
        "device_name": "OldAgent",
        "chipset": "Snapdragon 888",
        "android_api": 31,
        "ram_gb": 6.0,
        "shizuku_available": False,
    }
    r1 = await client.post("/devices/register", json=body)
    assert r1.status_code == 201
    first_id = r1.json()["device_id"]

    r2 = await client.post("/devices/register", json=body)
    assert r2.status_code == 201
    # Same fingerprint -> same id
    assert r2.json()["device_id"] == first_id


async def test_cors_preflight_allowed_origin(client: AsyncClient) -> None:
    """Preflight from emuflow.app must succeed and echo origin."""
    r = await client.options(
        "/devices/heartbeat",
        headers={
            "Origin": "https://emuflow.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "https://emuflow.app"
