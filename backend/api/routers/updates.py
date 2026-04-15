"""
EmuFlow API — Updates Router
Checks for emulator updates via GitHub releases API (Obtainium-compatible).
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("emuflow.updates")
router = APIRouter()

# ---------------------------------------------------------------------------
# Emulator GitHub repository registry
# ---------------------------------------------------------------------------

EMULATOR_REPOS: dict[str, dict[str, str]] = {
    "retroarch": {
        "owner": "libretro",
        "repo": "RetroArch",
        "display_name": "RetroArch",
    },
    "dolphin": {
        "owner": "dolphin-emu",
        "repo": "dolphin",
        "display_name": "Dolphin Emulator",
    },
    "ppsspp": {
        "owner": "hrydgard",
        "repo": "ppsspp",
        "display_name": "PPSSPP",
    },
    "nethersx2": {
        "owner": "Trixarian",
        "repo": "NetherSX2-classic",
        "display_name": "NetherSX2",
    },
    "lime3ds": {
        "owner": "Lime3DS",
        "repo": "Lime3DS",
        "display_name": "Lime3DS",
    },
    "esde": {
        "owner": "es-de",
        "repo": "es-de",
        "display_name": "ES-DE Frontend",
    },
    "obtainium": {
        "owner": "ImranR98",
        "repo": "Obtainium",
        "display_name": "Obtainium",
    },
}

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_last_check_results: dict[str, dict] = {}
_last_check_time: Optional[datetime] = None
_scheduled_interval_hours: Optional[float] = None


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ScheduleRequest(BaseModel):
    """Request to schedule periodic update checks."""

    interval_hours: float = 6.0


class EmulatorUpdateInfo(BaseModel):
    """Update information for a single emulator."""

    emulator: str
    display_name: str
    owner: str
    repo: str
    latest_version: Optional[str] = None
    release_url: Optional[str] = None
    published_at: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fetch_latest_release(
    client: httpx.AsyncClient,
    emulator_id: str,
    info: dict[str, str],
) -> dict:
    """
    Fetch the latest GitHub release for one emulator.

    Returns a dict with version, URL, and publish date (or an error message).
    """
    owner = info["owner"]
    repo = info["repo"]
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    try:
        response = await client.get(
            url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "emulator": emulator_id,
            "display_name": info["display_name"],
            "owner": owner,
            "repo": repo,
            "latest_version": data.get("tag_name"),
            "release_url": data.get("html_url"),
            "published_at": data.get("published_at"),
            "error": None,
        }
    except httpx.HTTPStatusError as exc:
        error_msg = f"HTTP {exc.response.status_code}"
        logger.warning("Failed to fetch release for %s/%s: %s", owner, repo, error_msg)
        return {
            "emulator": emulator_id,
            "display_name": info["display_name"],
            "owner": owner,
            "repo": repo,
            "latest_version": None,
            "release_url": None,
            "published_at": None,
            "error": error_msg,
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error fetching %s/%s: %s", owner, repo, exc)
        return {
            "emulator": emulator_id,
            "display_name": info["display_name"],
            "owner": owner,
            "repo": repo,
            "latest_version": None,
            "release_url": None,
            "published_at": None,
            "error": str(exc),
        }


async def _run_update_check() -> dict[str, dict]:
    """
    Check all registered emulator repos concurrently and store results.
    """
    global _last_check_results, _last_check_time

    async with httpx.AsyncClient() as client:
        tasks = [
            _fetch_latest_release(client, emu_id, info)
            for emu_id, info in EMULATOR_REPOS.items()
        ]
        results = await asyncio.gather(*tasks)

    _last_check_results = {r["emulator"]: r for r in results}
    _last_check_time = datetime.now(timezone.utc)
    logger.info("Update check completed at %s", _last_check_time.isoformat())
    return _last_check_results


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/check", summary="Check for emulator updates")
async def check_updates() -> dict:
    """
    Fetch the latest release information from GitHub for all registered
    emulators and return the results immediately.

    Uses the GitHub Releases API endpoint:
    ``GET https://api.github.com/repos/{owner}/{repo}/releases/latest``
    """
    results = await _run_update_check()
    return {
        "checked_at": _last_check_time.isoformat() if _last_check_time else None,
        "emulators": results,
    }


@router.post("/schedule", summary="Schedule periodic update checks")
async def schedule_updates(
    payload: ScheduleRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Store the requested interval and trigger an immediate background check.

    Note: In an MVP without a task queue (Celery/APScheduler), this records
    the desired interval and performs one immediate check. A persistent
    scheduler can read ``_scheduled_interval_hours`` to set up recurring jobs.
    """
    global _scheduled_interval_hours
    _scheduled_interval_hours = payload.interval_hours

    background_tasks.add_task(_run_update_check)

    return {
        "message": (
            f"Update check scheduled every {payload.interval_hours} hour(s). "
            "An immediate check has been queued in the background."
        ),
        "interval_hours": payload.interval_hours,
    }


@router.get("/status", summary="Get last update check results")
async def get_update_status() -> dict:
    """
    Return the cached results from the most recent update check without
    hitting the GitHub API again.
    """
    if not _last_check_results:
        return {
            "checked_at": None,
            "scheduled_interval_hours": _scheduled_interval_hours,
            "message": "No update check has been performed yet. Call GET /updates/check first.",
            "emulators": {},
        }

    return {
        "checked_at": _last_check_time.isoformat() if _last_check_time else None,
        "scheduled_interval_hours": _scheduled_interval_hours,
        "emulators": _last_check_results,
    }
