"""
EmuFlow - Update Scheduler
Periodic emulator update checking powered by APScheduler.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .obtainium_service import EmulatorUpdateResult, ObtainiumService

logger = logging.getLogger(__name__)

CACHE_FILE = "/tmp/emuflow_update_cache.json"
JOB_ID = "emuflow_update_check"

# Type alias for the notification callback
UpdateCallback = Callable[[str, str, str], Awaitable[None]]


class UpdateScheduler:
    """Manages periodic emulator update checks and persists results to a JSON
    cache file.

    Example usage::

        scheduler = UpdateScheduler(on_update_found=my_callback)
        scheduler.start(interval_hours=12)
        ...
        scheduler.stop()
    """

    def __init__(
        self,
        github_token: str | None = None,
        on_update_found: UpdateCallback | None = None,
    ) -> None:
        """
        Args:
            github_token: Optional GitHub API token for higher rate limits.
            on_update_found: Async callback invoked when a new version is
                detected.  Signature: ``async (emulator_id, old_version,
                new_version) -> None``.
        """
        self._service = ObtainiumService(github_token=github_token)
        self._on_update_found = on_update_found
        self._scheduler = AsyncIOScheduler()
        self._running = False

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_cache() -> dict[str, Any]:
        """Read the on-disk cache.  Returns an empty dict on any error."""
        if not os.path.exists(CACHE_FILE):
            return {}
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read update cache: %s", exc)
            return {}

    @staticmethod
    def _save_cache(data: dict[str, Any]) -> None:
        """Persist data to the on-disk cache."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.error("Could not write update cache: %s", exc)

    # ------------------------------------------------------------------
    # Core job
    # ------------------------------------------------------------------

    async def _run_check(self) -> dict[str, Any]:
        """Run a full update check and persist results.

        Returns:
            Dict ready to be serialised or returned via the API.
        """
        logger.info("Starting emulator update check …")
        old_cache = self._load_cache()
        old_versions: dict[str, str] = {
            eid: entry.get("latest_version", "")
            for eid, entry in old_cache.get("results", {}).items()
        }

        results: dict[str, EmulatorUpdateResult] = await self._service.check_all_emulators()

        serialised: dict[str, Any] = {}
        for eid, result in results.items():
            serialised[eid] = asdict(result)

            # Notify if a new version was found
            old_ver = old_versions.get(eid, "")
            new_ver = result.latest_version
            if old_ver and new_ver and old_ver != new_ver and not result.error:
                logger.info(
                    "Update found for %s: %s → %s", eid, old_ver, new_ver
                )
                if self._on_update_found is not None:
                    try:
                        await self._on_update_found(eid, old_ver, new_ver)
                    except Exception as exc:  # noqa: BLE001
                        logger.error(
                            "on_update_found callback raised an error: %s", exc
                        )

        payload: dict[str, Any] = {
            "results": serialised,
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "errors": sum(1 for r in results.values() if r.error),
        }
        self._save_cache(payload)
        logger.info(
            "Update check complete. %d emulators checked, %d errors.",
            payload["total"],
            payload["errors"],
        )
        return payload

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, interval_hours: int = 24) -> None:
        """Start the scheduler with the given interval.

        If the scheduler is already running, the existing job is replaced.

        Args:
            interval_hours: How often to run the update check, in hours.
        """
        if self._scheduler.running:
            # Replace the existing job with the new interval
            try:
                self._scheduler.remove_job(JOB_ID)
            except Exception:  # noqa: BLE001
                pass
        else:
            self._scheduler.start()

        trigger = IntervalTrigger(hours=interval_hours)
        self._scheduler.add_job(
            self._run_check,
            trigger=trigger,
            id=JOB_ID,
            name="EmuFlow emulator update check",
            replace_existing=True,
            misfire_grace_time=300,  # 5-minute grace period
        )
        self._running = True
        logger.info(
            "Update scheduler started (interval: %d h). Next run: %s",
            interval_hours,
            self._scheduler.get_job(JOB_ID).next_run_time,
        )

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        self._running = False
        logger.info("Update scheduler stopped.")

    async def run_now(self) -> dict[str, Any]:
        """Trigger an immediate update check outside the normal schedule.

        Returns:
            The full check result payload (same format as the cache file).
        """
        logger.info("Manual update check triggered.")
        return await self._run_check()

    @property
    def is_running(self) -> bool:
        """True if the scheduler is active."""
        return self._running and self._scheduler.running

    def get_next_run_time(self) -> str | None:
        """Return the ISO timestamp of the next scheduled run, or None."""
        if not self._scheduler.running:
            return None
        job = self._scheduler.get_job(JOB_ID)
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None
