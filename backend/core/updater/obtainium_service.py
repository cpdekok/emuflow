"""
EmuFlow - Obtainium Service
Emulator update checking via GitHub API using async httpx.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Emulator source definitions
# ---------------------------------------------------------------------------

EMULATOR_SOURCES: dict[str, dict[str, str]] = {
    "retroarch": {
        "github": "libretro/RetroArch",
        "apk_filter": "RetroArch_aarch64.apk",
        "display_name": "RetroArch",
        "category": "frontend",
    },
    "dolphin": {
        "github": "dolphin-emu/dolphin",
        "apk_filter": "dolphin-",
        "display_name": "Dolphin Emulator",
        "category": "standalone",
    },
    "ppsspp": {
        "github": "hrydgard/ppsspp",
        "apk_filter": "PPSSPP",
        "display_name": "PPSSPP",
        "category": "standalone",
    },
    "nethersx2": {
        "github": "Trixarian/NetherSX2-patch",
        "apk_filter": ".apk",
        "display_name": "NetherSX2",
        "category": "standalone",
    },
    "lime3ds": {
        "github": "Lime3DS/Lime3DS",
        "apk_filter": "app-arm64",
        "display_name": "Lime3DS",
        "category": "standalone",
    },
    "es_de": {
        "github": "ES-DE/emulationstation-de",
        "apk_filter": "ES-DE",
        "display_name": "ES-DE Frontend",
        "category": "frontend",
    },
    "obtainium": {
        "github": "ImranR98/Obtainium",
        "apk_filter": "app-arm64-v8a-release",
        "display_name": "Obtainium",
        "category": "tool",
    },
    "sudachi": {
        "github": "sudachi-emu/sudachi",
        "apk_filter": "app-arm64",
        "display_name": "Sudachi (Switch)",
        "category": "standalone",
    },
}

GITHUB_API_BASE = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

MAX_CHANGELOG_LENGTH = 500


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class EmulatorUpdateResult:
    emulator_id: str
    display_name: str
    latest_version: str
    published_at: str
    download_url: str | None
    changelog_snippet: str
    check_timestamp: str
    error: str | None = None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ObtainiumService:
    """Checks GitHub releases for emulator updates and generates Obtainium-
    compatible import JSON."""

    def __init__(self, github_token: str | None = None) -> None:
        """
        Args:
            github_token: Optional GitHub personal access token to increase
                          the API rate limit from 60 to 5 000 req/h.
        """
        self._token = github_token
        self._headers = dict(GITHUB_HEADERS)
        if github_token:
            self._headers["Authorization"] = f"Bearer {github_token}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=self._headers,
            timeout=httpx.Timeout(15.0),
            follow_redirects=True,
        )

    @staticmethod
    def _pick_download_url(assets: list[dict[str, Any]], apk_filter: str) -> str | None:
        """Return the browser_download_url of the first asset whose name
        contains *apk_filter* (case-insensitive)."""
        needle = apk_filter.lower()
        for asset in assets:
            name: str = asset.get("name", "")
            if needle in name.lower():
                return asset.get("browser_download_url")
        return None

    @staticmethod
    def _truncate_changelog(body: str | None) -> str:
        if not body:
            return ""
        body = body.strip()
        if len(body) <= MAX_CHANGELOG_LENGTH:
            return body
        return body[:MAX_CHANGELOG_LENGTH].rsplit(" ", 1)[0] + " …"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check_single_emulator(self, emulator_id: str) -> EmulatorUpdateResult:
        """Fetch the latest GitHub release for one emulator.

        Args:
            emulator_id: Key from :data:`EMULATOR_SOURCES`.

        Returns:
            :class:`EmulatorUpdateResult` with version information, or an
            instance with ``error`` set if the request fails.
        """
        source = EMULATOR_SOURCES.get(emulator_id)
        if source is None:
            return EmulatorUpdateResult(
                emulator_id=emulator_id,
                display_name=emulator_id,
                latest_version="",
                published_at="",
                download_url=None,
                changelog_snippet="",
                check_timestamp=self._now_iso(),
                error=f"Unknown emulator_id: '{emulator_id}'",
            )

        owner_repo = source["github"]
        url = f"{GITHUB_API_BASE}/repos/{owner_repo}/releases/latest"

        try:
            async with self._make_client() as client:
                response = await client.get(url)

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "unknown")
                    raise RuntimeError(
                        f"GitHub API rate limit exceeded. Retry after {retry_after}s."
                    )

                if response.status_code == 404:
                    raise RuntimeError(
                        f"Repository '{owner_repo}' not found or has no releases."
                    )

                response.raise_for_status()
                data: dict[str, Any] = response.json()

        except httpx.TimeoutException as exc:
            return EmulatorUpdateResult(
                emulator_id=emulator_id,
                display_name=source["display_name"],
                latest_version="",
                published_at="",
                download_url=None,
                changelog_snippet="",
                check_timestamp=self._now_iso(),
                error=f"Request timed out: {exc}",
            )
        except httpx.NetworkError as exc:
            return EmulatorUpdateResult(
                emulator_id=emulator_id,
                display_name=source["display_name"],
                latest_version="",
                published_at="",
                download_url=None,
                changelog_snippet="",
                check_timestamp=self._now_iso(),
                error=f"Network error: {exc}",
            )
        except httpx.HTTPStatusError as exc:
            return EmulatorUpdateResult(
                emulator_id=emulator_id,
                display_name=source["display_name"],
                latest_version="",
                published_at="",
                download_url=None,
                changelog_snippet="",
                check_timestamp=self._now_iso(),
                error=f"HTTP error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except RuntimeError as exc:
            return EmulatorUpdateResult(
                emulator_id=emulator_id,
                display_name=source["display_name"],
                latest_version="",
                published_at="",
                download_url=None,
                changelog_snippet="",
                check_timestamp=self._now_iso(),
                error=str(exc),
            )

        tag_name: str = data.get("tag_name", "")
        published_at: str = data.get("published_at", "")
        body: str = data.get("body", "") or ""
        assets: list[dict[str, Any]] = data.get("assets", [])

        download_url = self._pick_download_url(assets, source["apk_filter"])
        if download_url is None:
            logger.warning(
                "No APK matching filter '%s' found in release assets for '%s'.",
                source["apk_filter"],
                emulator_id,
            )

        return EmulatorUpdateResult(
            emulator_id=emulator_id,
            display_name=source["display_name"],
            latest_version=tag_name,
            published_at=published_at,
            download_url=download_url,
            changelog_snippet=self._truncate_changelog(body),
            check_timestamp=self._now_iso(),
        )

    async def check_all_emulators(self) -> dict[str, EmulatorUpdateResult]:
        """Check all emulators in :data:`EMULATOR_SOURCES` concurrently.

        Returns:
            Mapping of emulator_id → :class:`EmulatorUpdateResult`.
        """
        emulator_ids = list(EMULATOR_SOURCES.keys())
        tasks = [self.check_single_emulator(eid) for eid in emulator_ids]
        results: list[EmulatorUpdateResult] = await asyncio.gather(*tasks)
        return {r.emulator_id: r for r in results}

    async def get_changelog(self, emulator_id: str, version: str) -> str:
        """Fetch the release notes for a specific version tag.

        Falls back to the latest release if the exact tag cannot be found.

        Args:
            emulator_id: Key from :data:`EMULATOR_SOURCES`.
            version: Git tag name (e.g. ``"v1.9.14"``).

        Returns:
            Release notes truncated to :data:`MAX_CHANGELOG_LENGTH` characters,
            or an error string.
        """
        source = EMULATOR_SOURCES.get(emulator_id)
        if source is None:
            return f"Unknown emulator_id: '{emulator_id}'"

        owner_repo = source["github"]
        # Try tag-specific endpoint first, fall back to latest.
        tag_url = f"{GITHUB_API_BASE}/repos/{owner_repo}/releases/tags/{version}"
        latest_url = f"{GITHUB_API_BASE}/repos/{owner_repo}/releases/latest"

        try:
            async with self._make_client() as client:
                response = await client.get(tag_url)
                if response.status_code == 404:
                    response = await client.get(latest_url)
                if response.status_code == 429:
                    return "GitHub API rate limit exceeded. Please try again later."
                response.raise_for_status()
                data: dict[str, Any] = response.json()
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            return f"Error fetching changelog: {exc}"

        body: str = data.get("body", "") or ""
        return self._truncate_changelog(body) or "No changelog available."

    def generate_obtainium_json(self, emulator_ids: list[str]) -> dict[str, Any]:
        """Generate an Obtainium-compatible import JSON for the given emulators.

        The returned dict can be serialised to JSON and imported directly into
        the Obtainium app.

        Args:
            emulator_ids: List of keys from :data:`EMULATOR_SOURCES`. Unknown
                          IDs are silently skipped.

        Returns:
            Dict matching Obtainium's import/export format.
        """
        apps: list[dict[str, Any]] = []

        for eid in emulator_ids:
            source = EMULATOR_SOURCES.get(eid)
            if source is None:
                logger.warning("generate_obtainium_json: unknown emulator_id '%s', skipping.", eid)
                continue

            owner_repo = source["github"]
            app_entry: dict[str, Any] = {
                "id": f"https://github.com/{owner_repo}",
                "url": f"https://github.com/{owner_repo}",
                "author": owner_repo.split("/")[0],
                "name": source["display_name"],
                "installedVersion": None,
                "latestVersion": None,
                "latestVersionCode": None,
                "apkUrls": [],
                "apkExtractionRegex": source["apk_filter"],
                "trackOnly": False,
                "versionExtractionRegex": None,
                "compareMethod": None,
                "additionalSettings": json.dumps(
                    {
                        "apkFilterRegEx": source["apk_filter"],
                        "invertAPKFilter": False,
                        "autoApkFilterByArch": False,
                        "releaseAsset": source["apk_filter"],
                    }
                ),
                "lastUpdateCheck": None,
                "pinned": False,
                "categories": [source["category"]],
                "releaseDate": None,
                "changeLog": None,
                "overrideSource": None,
            }
            apps.append(app_entry)

        return {
            "apps": apps,
            "exported_at": self._now_iso(),
            "obtainium_version": "emuflow-generated",
        }
