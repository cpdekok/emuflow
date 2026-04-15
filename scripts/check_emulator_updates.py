#!/usr/bin/env python3
"""
EmuFlow — Emulator Update Checker Script
Gebruik: python scripts/check_emulator_updates.py

Controleert GitHub releases voor alle ondersteunde emulatoren.
Genereert update_report.json als er updates zijn.
Gebruikt dezelfde EMULATOR_SOURCES als de backend ObtainiumService.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx niet geïnstalleerd. Voer uit: pip install httpx")
    sys.exit(1)

EMULATOR_SOURCES = {
    "retroarch": {
        "github": "libretro/RetroArch",
        "apk_filter": "RetroArch_aarch64.apk",
        "display_name": "RetroArch",
    },
    "dolphin": {
        "github": "dolphin-emu/dolphin",
        "apk_filter": "dolphin-",
        "display_name": "Dolphin Emulator",
    },
    "ppsspp": {
        "github": "hrydgard/ppsspp",
        "apk_filter": "PPSSPP",
        "display_name": "PPSSPP",
    },
    "nethersx2": {
        "github": "Trixarian/NetherSX2-patch",
        "apk_filter": ".apk",
        "display_name": "NetherSX2",
    },
    "lime3ds": {
        "github": "Lime3DS/Lime3DS",
        "apk_filter": "app-arm64",
        "display_name": "Lime3DS",
    },
    "es_de": {
        "github": "ES-DE/emulationstation-de",
        "apk_filter": "ES-DE",
        "display_name": "ES-DE Frontend",
    },
    "obtainium": {
        "github": "ImranR98/Obtainium",
        "apk_filter": "app-arm64-v8a-release",
        "display_name": "Obtainium",
    },
    "sudachi": {
        "github": "sudachi-emu/sudachi",
        "apk_filter": "app-arm64",
        "display_name": "Sudachi",
    },
}

CACHE_FILE = Path(__file__).parent.parent / "tmp" / "last_versions.json"


async def check_emulator(client: httpx.AsyncClient, emulator_id: str, info: dict) -> dict:
    """Checkt de laatste release van een emulator op GitHub."""
    owner, repo = info["github"].split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = await client.get(url, headers=headers, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()

        # Zoek APK download URL
        download_url = None
        for asset in data.get("assets", []):
            if info["apk_filter"].lower() in asset["name"].lower():
                download_url = asset["browser_download_url"]
                break

        return {
            "emulator_id": emulator_id,
            "display_name": info["display_name"],
            "latest_version": data.get("tag_name", "unknown"),
            "published_at": data.get("published_at", ""),
            "download_url": download_url,
            "changelog_snippet": (data.get("body") or "")[:300],
            "check_timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
    except Exception as e:
        return {
            "emulator_id": emulator_id,
            "display_name": info["display_name"],
            "latest_version": None,
            "error": str(e),
            "check_timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def main():
    print(f"EmuFlow Update Checker — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Laad vorige versies
    last_versions = {}
    if CACHE_FILE.exists():
        try:
            last_versions = json.loads(CACHE_FILE.read_text())
        except Exception:
            pass

    async with httpx.AsyncClient() as client:
        tasks = [check_emulator(client, emu_id, info) for emu_id, info in EMULATOR_SOURCES.items()]
        results = await asyncio.gather(*tasks)

    updates_found = []
    current_versions = {}
    lines = []

    for result in results:
        emu_id = result["emulator_id"]
        if result.get("error"):
            print(f"  ✗ {result['display_name']}: ERROR — {result['error']}")
            continue

        version = result["latest_version"]
        current_versions[emu_id] = version
        prev_version = last_versions.get(emu_id)

        if prev_version and prev_version != version:
            status = f"UPDATE: {prev_version} → {version}"
            updates_found.append({"emulator": result["display_name"], "from": prev_version, "to": version})
            print(f"  ↑ {result['display_name']}: {status}")
        elif not prev_version:
            print(f"  + {result['display_name']}: {version} (eerste check)")
        else:
            print(f"  ✓ {result['display_name']}: {version} (actueel)")

        if result.get("download_url"):
            lines.append(f"- **{result['display_name']}** `{version}`: [{result['download_url']}]({result['download_url']})")

    # Sla nieuwe versies op
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(current_versions, indent=2))

    # Genereer rapport als er updates zijn
    if updates_found:
        summary = "## Emulator Updates Beschikbaar\n\n"
        summary += f"Gecontroleerd op: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        summary += "| Emulator | Van | Naar |\n|----------|-----|------|\n"
        for u in updates_found:
            summary += f"| {u['emulator']} | `{u['from']}` | `{u['to']}` |\n"
        summary += "\n\n### Download Links\n" + "\n".join(lines)

        report = {"updates_found": updates_found, "summary": summary, "checked_at": datetime.now().isoformat()}
        Path("update_report.json").write_text(json.dumps(report, indent=2))
        print(f"\n{len(updates_found)} update(s) gevonden. Rapport opgeslagen: update_report.json")
    else:
        print("\nAlle emulatoren zijn actueel.")


if __name__ == "__main__":
    asyncio.run(main())
