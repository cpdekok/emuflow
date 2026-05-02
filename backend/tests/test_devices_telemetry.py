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


def _rp_mini_payload(**overrides: object) -> dict:
    """Retroid Pocket Mini full Phase-1 heartbeat payload."""
    base: dict[str, object] = {
        "hardware_fingerprint": "fp-rpmini-" + "c" * 26,
        "device_name": "Retroid Pocket Mini",
        "chipset": "Dimensity 1100",
        "android_api": 33,
        "ram_gb": 8.0,
        "shizuku_available": True,
        "agent_version": "0.3.0",
        # Phase 1 new fields
        "manufacturer": "Retroid",
        "model": "RP Mini",
        "android_release": "13",
        "soc_vendor": "MediaTek",
        "soc_chip": "MT6891",
        "gpu_family": "Mali-G77",
        "page_size": 4096,
        "ram_mb": 8192,
        "shizuku_version": 13,
        "is_rooted": False,
        "has_analog_sticks": True,
        "controller_layout": "dual_stick",
        "vendor_shell_packages": ["com.retroid.launcher"],
        "thermal_state": "nominal",
        "battery_level": 78.5,
        "battery_temperature_c": 32.1,
        "save_events_24h": {
            "saves_total": 5,
            "saves_per_emulator": {"org.dolphinemu.dolphinemu": 3, "com.retroarch": 2},
            "vault_size_mb": 42,
            "vault_versions_total": 12,
            "backup_failures_24h": 0,
        },
    }
    base.update(overrides)
    return base


def _ayaneo_payload(**overrides: object) -> dict:
    """AYANEO Pocket Micro Classic full Phase-1 heartbeat payload."""
    base: dict[str, object] = {
        "hardware_fingerprint": "fp-ayaneo-" + "d" * 26,
        "device_name": "AYANEO Pocket Micro Classic",
        "chipset": "Snapdragon 8 Gen 2",
        "android_api": 34,
        "ram_gb": 12.0,
        "shizuku_available": True,
        "agent_version": "0.3.0",
        "manufacturer": "AYANEO",
        "model": "Pocket Micro Classic",
        "android_release": "14",
        "soc_vendor": "Qualcomm",
        "soc_chip": "SM8550",
        "gpu_family": "Adreno 740",
        "page_size": 16384,
        "ram_mb": 12288,
        "shizuku_version": 15,
        "is_rooted": False,
        "has_analog_sticks": True,
        "controller_layout": "dual_stick",
        "vendor_shell_packages": ["com.ayaneo.launcher"],
        "thermal_state": "nominal",
        "battery_level": 55.0,
        "battery_temperature_c": 30.0,
    }
    base.update(overrides)
    return base


def _crash_payload(hardware_fingerprint: str, **overrides: object) -> dict:
    base: dict[str, object] = {
        "hardware_fingerprint": hardware_fingerprint,
        "timestamp": "2026-05-01T12:00:00Z",
        "emulator_package": "org.dolphinemu.dolphinemu",
        "emulator_version_name": "5.0-21000",
        "emulator_version_code": 21000,
        "game_id": "GALE01",
        "platform": "gc",
        "duration_played_sec": 3600,
        "crash_reason": "SIGSEGV in libdolphin.so",
        "crash_signal": "SIGSEGV",
        "rss_mb": 512,
        "pss_mb": 480,
        "stacktrace_hash": "abc123def456" + "0" * 52,
        "tombstone_excerpt": "signal 11 (SIGSEGV), code 1...",
        "thermal_state": "hot",
        "battery_level": 45.0,
        "battery_temperature_c": 38.5,
        "free_ram_mb": 256,
        "page_size": 4096,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Heartbeat upsert — existing tests
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
# Heartbeat backwards-compatibility — minimal payload without Phase-1 fields
# ---------------------------------------------------------------------------


async def test_heartbeat_without_new_fields_backwards_compat(client: AsyncClient) -> None:
    """Old agents that don't send Phase-1 fields must still work fine."""
    minimal = {
        "hardware_fingerprint": "fp-minimal-" + "e" * 25,
        "device_name": "Old Agent Phone",
        "chipset": "Exynos 2200",
        "android_api": 31,
        "ram_gb": 6.0,
        # No Phase-1 fields at all
    }
    res = await client.post("/devices/heartbeat", json=minimal)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["device_id"]
    assert body["online"] is True

    async with database.SessionLocal() as s:
        rows = (await s.execute(select(Device))).scalars().all()
        assert len(rows) == 1
        dev = rows[0]
        # Phase-1 fields should be None / default
        assert dev.manufacturer is None
        assert dev.soc_vendor is None
        assert dev.is_rooted is False
        assert dev.has_analog_sticks is None
        assert dev.controller_layout is None


# ---------------------------------------------------------------------------
# Heartbeat with full Phase-1 fields — RP Mini
# ---------------------------------------------------------------------------


async def test_heartbeat_rp_mini_all_fields(client: AsyncClient) -> None:
    """Retroid Pocket Mini heartbeat with full Phase-1 payload."""
    res = await client.post("/devices/heartbeat", json=_rp_mini_payload())
    assert res.status_code == 200, res.text

    device_id = res.json()["device_id"]
    detail = await client.get(f"/devices/{device_id}")
    assert detail.status_code == 200
    d = detail.json()

    assert d["manufacturer"] == "Retroid"
    assert d["model"] == "RP Mini"
    assert d["android_release"] == "13"
    assert d["soc_vendor"] == "MediaTek"
    assert d["soc_chip"] == "MT6891"
    assert d["gpu_family"] == "Mali-G77"
    assert d["page_size"] == 4096
    assert d["ram_mb"] == 8192
    assert d["shizuku_version"] == 13
    assert d["is_rooted"] is False
    assert d["has_analog_sticks"] is True
    assert d["controller_layout"] == "dual_stick"
    assert d["vendor_shell_packages"] == ["com.retroid.launcher"]
    assert d["thermal_state"] == "nominal"
    assert d["battery_level"] == 78.5
    assert d["battery_temperature_c"] == 32.1
    assert d["last_heartbeat_at"] is not None

    # Save-events aggregates
    se = d["save_events_24h"]
    assert se is not None
    assert se["saves_total"] == 5
    assert se["vault_size_mb"] == 42
    assert se["backup_failures_24h"] == 0


# ---------------------------------------------------------------------------
# Heartbeat with full Phase-1 fields — AYANEO Pocket Micro Classic
# ---------------------------------------------------------------------------


async def test_heartbeat_ayaneo_pocket_micro_classic(client: AsyncClient) -> None:
    """AYANEO Pocket Micro Classic heartbeat with full Phase-1 payload."""
    res = await client.post("/devices/heartbeat", json=_ayaneo_payload())
    assert res.status_code == 200, res.text

    device_id = res.json()["device_id"]
    detail = await client.get(f"/devices/{device_id}")
    assert detail.status_code == 200
    d = detail.json()

    assert d["manufacturer"] == "AYANEO"
    assert d["model"] == "Pocket Micro Classic"
    assert d["soc_vendor"] == "Qualcomm"
    assert d["soc_chip"] == "SM8550"
    assert d["gpu_family"] == "Adreno 740"
    assert d["page_size"] == 16384
    assert d["ram_mb"] == 12288
    assert d["controller_layout"] == "dual_stick"


# ---------------------------------------------------------------------------
# Heartbeat — invalid controller_layout rejected
# ---------------------------------------------------------------------------


async def test_heartbeat_invalid_controller_layout(client: AsyncClient) -> None:
    """controller_layout must be one of dual_stick/no_stick/single_stick."""
    payload = _heartbeat_payload(controller_layout="turbo_stick")
    res = await client.post("/devices/heartbeat", json=payload)
    assert res.status_code == 422, res.text


# ---------------------------------------------------------------------------
# Crash-event POST endpoint
# ---------------------------------------------------------------------------


async def test_crash_event_post_success(client: AsyncClient) -> None:
    """Posting a crash event for a known device returns 201 with correct data."""
    # First, register the device via heartbeat
    hb = await client.post("/devices/heartbeat", json=_rp_mini_payload())
    assert hb.status_code == 200
    fp = _rp_mini_payload()["hardware_fingerprint"]

    crash = _crash_payload(fp)
    res = await client.post("/devices/crash-events", json=crash)
    assert res.status_code == 201, res.text
    body = res.json()

    assert body["id"]
    assert body["device_id"] == hb.json()["device_id"]
    assert body["emulator_package"] == "org.dolphinemu.dolphinemu"
    assert body["game_id"] == "GALE01"
    assert body["platform"] == "gc"
    assert body["crash_reason"] == "SIGSEGV in libdolphin.so"
    assert body["crash_signal"] == "SIGSEGV"
    assert body["created_at"] is not None


async def test_crash_event_unknown_device_404(client: AsyncClient) -> None:
    """Crash event for an unknown fingerprint returns 404."""
    crash = _crash_payload("fp-unknown-" + "z" * 25)
    res = await client.post("/devices/crash-events", json=crash)
    assert res.status_code == 404, res.text


async def test_crash_event_minimal_payload(client: AsyncClient) -> None:
    """Crash event with only required fields (hardware_fingerprint + timestamp)."""
    hb = await client.post("/devices/heartbeat", json=_heartbeat_payload())
    fp = _heartbeat_payload()["hardware_fingerprint"]

    minimal_crash = {
        "hardware_fingerprint": fp,
        "timestamp": "2026-05-01T15:00:00Z",
    }
    res = await client.post("/devices/crash-events", json=minimal_crash)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["game_id"] is None
    assert body["emulator_package"] is None


# ---------------------------------------------------------------------------
# Response models contain new Phase-1 fields
# ---------------------------------------------------------------------------


async def test_device_list_contains_phase1_fields(client: AsyncClient) -> None:
    """GET /devices response includes Phase-1 fields."""
    await client.post("/devices/heartbeat", json=_rp_mini_payload())
    res = await client.get("/devices")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    d = items[0]

    # All Phase-1 fields must be present in response schema
    for field in [
        "manufacturer", "model", "android_release",
        "soc_vendor", "soc_chip", "gpu_family",
        "page_size", "ram_mb", "shizuku_version",
        "is_rooted", "has_analog_sticks", "controller_layout",
        "vendor_shell_packages", "thermal_state",
        "battery_level", "battery_temperature_c",
        "last_heartbeat_at", "save_events_24h",
    ]:
        assert field in d, f"Field '{field}' missing from DeviceListItem response"


async def test_device_detail_contains_phase1_fields(client: AsyncClient) -> None:
    """GET /devices/{id} response includes Phase-1 fields."""
    hb = await client.post("/devices/heartbeat", json=_ayaneo_payload())
    device_id = hb.json()["device_id"]

    res = await client.get(f"/devices/{device_id}")
    assert res.status_code == 200
    d = res.json()

    assert "manufacturer" in d
    assert "soc_vendor" in d
    assert "controller_layout" in d
    assert "save_events_24h" in d
    assert "last_heartbeat_at" in d
    # last_known_ip is admin-only — should NOT appear in DeviceDetail
    assert "last_known_ip" not in d


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


# ---------------------------------------------------------------------------
# Blueprint 17 + 18: ROM-library and launcher report endpoints
# ---------------------------------------------------------------------------


async def test_library_scan_post_and_get(client: AsyncClient) -> None:
    """Agent posts aggregated counts, frontend reads them back."""
    # 1) Heartbeat first to register the device.
    fp = "fp-lib-" + "x" * 30
    r = await client.post("/devices/heartbeat", json=_heartbeat_payload(hardware_fingerprint=fp))
    assert r.status_code == 200
    device_id = r.json()["device_id"]

    # 2) Agent posts library scan.
    payload = {
        "hardware_fingerprint": fp,
        "total_count": 423,
        "by_platform": {"snes": 120, "psx": 80, "gb": 50},
        "preinstalled_count": 3,
        "duplicate_groups_exact": 1,
        "duplicate_groups_probable": 2,
        "language_candidates": 7,
    }
    r2 = await client.post("/devices/library/scan-results", json=payload)
    assert r2.status_code == 200
    body = r2.json()
    assert body["device_id"] == device_id
    assert body["total_count"] == 423
    assert body["preinstalled_count"] == 3
    assert body["by_platform"]["snes"] == 120

    # 3) Frontend GET returns the same record.
    r3 = await client.get(f"/devices/{device_id}/library")
    assert r3.status_code == 200
    assert r3.json()["total_count"] == 423


async def test_library_get_unknown_device_returns_404(client: AsyncClient) -> None:
    r = await client.get("/devices/00000000-0000-0000-0000-000000000000/library")
    assert r.status_code == 404


async def test_library_post_unknown_fingerprint_returns_404(client: AsyncClient) -> None:
    r = await client.post(
        "/devices/library/scan-results",
        json={
            "hardware_fingerprint": "fp-unknown-" + "z" * 30,
            "total_count": 1,
        },
    )
    assert r.status_code == 404


async def test_launcher_report_post_and_get(client: AsyncClient) -> None:
    fp = "fp-lau-" + "y" * 30
    r = await client.post("/devices/heartbeat", json=_heartbeat_payload(hardware_fingerprint=fp))
    assert r.status_code == 200
    device_id = r.json()["device_id"]

    payload = {
        "hardware_fingerprint": fp,
        "active_home_package": "com.magneticchen.daijishou",
        "detected": [
            {
                "package_name": "com.magneticchen.daijishou",
                "display_name": "Daijisho",
                "is_default_home": True,
                "is_installed": True,
                "boxart_capability": "auto",
                "video_capability": "auto",
                "notes": "TapiocaFox CDN streaming",
            },
            {
                "package_name": "org.es_de.frontend",
                "display_name": "ES-DE",
                "is_default_home": False,
                "is_installed": True,
                "boxart_capability": "auto",
                "video_capability": "auto",
                "notes": "ScreenScraper account required",
            },
        ],
    }
    r2 = await client.post("/devices/launchers/report", json=payload)
    assert r2.status_code == 200
    assert r2.json()["device_id"] == device_id
    assert len(r2.json()["detected"]) == 2

    r3 = await client.get(f"/devices/{device_id}/launchers")
    assert r3.status_code == 200
    body = r3.json()
    assert body["active_home_package"] == "com.magneticchen.daijishou"
    assert body["detected"][0]["display_name"] == "Daijisho"
