"""
EmuFlow - Knowledge Base
Static knowledge for the AI support agent: known issues, FAQs, hotkeys, and
BIOS information for popular Android emulators.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Known issues & solutions
# ---------------------------------------------------------------------------

KNOWN_ISSUES: dict[str, dict[str, str]] = {
    "retroarch_black_screen": {
        "problem": "RetroArch shows a black screen after loading a ROM.",
        "solution": (
            "1. Confirm the correct core is selected for your game format. "
            "2. Check Settings → Video → Video Driver; try switching between Vulkan and GLSL. "
            "3. Ensure your BIOS files are in the correct folder (Settings → Directory → System/BIOS). "
            "4. Try disabling 'Threaded Video' (Settings → Video → Threading)."
        ),
        "category": "installation",
    },
    "retroarch_no_audio": {
        "problem": "RetroArch has no audio or sound is distorted.",
        "solution": (
            "1. Go to Settings → Audio and ensure 'Audio' is enabled. "
            "2. Try switching the Audio Driver (e.g. from OpenSL to AAudio). "
            "3. Increase the Audio Latency slider slightly. "
            "4. Disable 'Audio Resampler' overrides in Quick Menu → Options."
        ),
        "category": "installation",
    },
    "retroarch_slow_performance": {
        "problem": "RetroArch runs slowly or drops frames.",
        "solution": (
            "1. Enable 'Run-Ahead' only if your device can handle it; otherwise disable it. "
            "2. Lower the internal resolution in Quick Menu → Options → Core Options. "
            "3. Use the Vulkan video driver for modern ARM devices. "
            "4. Set the CPU clock governor to Performance in Android developer options."
        ),
        "category": "hardware",
    },
    "dolphin_controller_not_detected": {
        "problem": "Dolphin does not detect the physical controller.",
        "solution": (
            "1. Open Dolphin → Settings → GameCube and select 'Standard Controller' for each port. "
            "2. Go to Config → GameCube → Port 1 → Configure and press 'Refresh'. "
            "3. On Android, ensure the app has permission to read game controllers. "
            "4. Try reconnecting the controller via Bluetooth or USB."
        ),
        "category": "controls",
    },
    "ppsspp_bios_missing": {
        "problem": "PPSSPP shows 'PSP firmware not found' or game fails to boot.",
        "solution": (
            "PPSSPP does not require the PSP firmware to run most games. "
            "If a game specifically needs it, place 'ppge_font_14.pgf' or the full firmware in "
            "/PSP/SYSTEM/ inside your PPSSPP memstick folder. "
            "Most homebrew and commercial games work without firmware."
        ),
        "category": "bios",
    },
    "nethersx2_low_fps": {
        "problem": "NetherSX2 (AetherSX2 fork) runs at low frame rates.",
        "solution": (
            "1. Set EE Cycle Rate to 100% or slightly lower in System settings. "
            "2. Enable 'Async Readbacks' and 'Async Texture Uploads'. "
            "3. Use OpenGL ES renderer; Vulkan may be less stable on some devices. "
            "4. Disable VU Stealing. "
            "5. Close background apps and set your device to maximum performance mode."
        ),
        "category": "hardware",
    },
    "lime3ds_no_audio": {
        "problem": "Lime3DS (3DS emulator) has missing or garbled audio.",
        "solution": (
            "1. In Lime3DS Settings → Audio, try switching from OpenAL to AAudio/SDL2. "
            "2. Ensure the latency setting matches your device; 100 ms is a safe default. "
            "3. Some games have broken audio in HLE mode; switch to LLE audio if available."
        ),
        "category": "installation",
    },
    "es_de_roms_not_showing": {
        "problem": "ES-DE does not show my ROMs.",
        "solution": (
            "1. Make sure your ROM folder path matches the path set in ES-DE Main Menu → Settings → Configure ROM directory. "
            "2. Use the correct subfolder names (e.g. 'nes', 'snes', 'psx') — see the ES-DE User Guide for the full list. "
            "3. Press Start → Quit ES-DE and re-launch so it scans the library. "
            "4. Check that ROM file extensions are supported for the system."
        ),
        "category": "frontend",
    },
    "obtainium_update_failed": {
        "problem": "Obtainium fails to check for updates or download APKs.",
        "solution": (
            "1. Ensure internet access is available. "
            "2. Check if GitHub is accessible; Obtainium uses the GitHub releases API. "
            "3. Update Obtainium itself first — older versions may hit API changes. "
            "4. For private repos, add a GitHub personal access token in Obtainium settings."
        ),
        "category": "update",
    },
}

# ---------------------------------------------------------------------------
# Per-emulator FAQs
# ---------------------------------------------------------------------------

EMULATOR_FAQS: dict[str, list[dict[str, str]]] = {
    "retroarch": [
        {
            "question": "Welke cores moet ik gebruiken voor SNES?",
            "answer": (
                "Snes9x is de beste keuze voor brede compatibiliteit. "
                "bsnes / bsnes-mercury accuracy zijn nauwkeuriger maar vereisen meer rekenkracht. "
                "Mesen-S is uitstekend voor hacks en accuraatheid."
            ),
        },
        {
            "question": "Hoe sla ik save states op in RetroArch?",
            "answer": (
                "Standaard hotkey: SELECT + R (opslaan) en SELECT + L (laden). "
                "Met RGC-standaard: MENU + R1 voor opslaan, MENU + L1 voor laden. "
                "Je kunt de slots wisselen via het Quick Menu (SELECT + X)."
            ),
        },
        {
            "question": "Waar plaats ik BIOS-bestanden voor RetroArch?",
            "answer": (
                "Ga naar Settings → Directory → System/BIOS en stel het pad in. "
                "Veelgebruikte locatie: /storage/emulated/0/RetroArch/system/. "
                "De bestandsnamen zijn hoofdlettergevoelig; gebruik exact de namen die de core verwacht."
            ),
        },
        {
            "question": "Hoe activeer ik shaders?",
            "answer": (
                "Open Quick Menu (SELECT + X) → Shaders → Load Shader Preset. "
                "Download extra shader packs via Online Updater → Update Shaders. "
                "Populaire keuzes: CRT-Royale voor retro look, xBRZ voor upscaling."
            ),
        },
    ],
    "ppsspp": [
        {
            "question": "Wat is de beste render-modus voor PPSSPP?",
            "answer": (
                "Gebruik Vulkan voor de beste prestaties op moderne Android-apparaten (Android 7+). "
                "Val terug op OpenGL ES als Vulkan instabiel is op jouw toestel."
            ),
        },
        {
            "question": "Hoe verbeter ik de prestaties in PPSSPP?",
            "answer": (
                "1. Zet rendering resolution op 2× of 1× voor zwakkere apparaten. "
                "2. Schakel 'Auto frameskip' in bij Settings → Graphics. "
                "3. Gebruik 'Fast memory (unstable)' alleen als een game te langzaam is."
            ),
        },
        {
            "question": "Hoe sla ik in PPSSPP games op?",
            "answer": (
                "PPSSPP ondersteunt zowel in-game saves als save states. "
                "Save states: gebruik de camera-icoon in het menu of configureer een knopcombo. "
                "In-game saves werken altijd via het standaard spaarmenu van de game."
            ),
        },
    ],
    "dolphin": [
        {
            "question": "Welke Android-versie is vereist voor Dolphin?",
            "answer": (
                "Dolphin vereist minimaal Android 5.0. "
                "Voor Vulkan-rendering is Android 7.0 of hoger aanbevolen. "
                "64-bit apparaten (ARM64) geven aanzienlijk betere prestaties."
            ),
        },
        {
            "question": "Hoe verbeter ik Wii/GameCube prestaties in Dolphin?",
            "answer": (
                "1. Gebruik Vulkan als grafische backend. "
                "2. Zet 'Synchronize GPU Thread' aan voor stabielere frametijden. "
                "3. Schakel 'Ubershaders' in op krachtige apparaten. "
                "4. Verlaag de interne resolutie naar 1× als het toestel moeite heeft."
            ),
        },
        {
            "question": "Hoe laad ik GameCube/Wii BIOS in Dolphin?",
            "answer": (
                "Dolphin heeft geen BIOS nodig om games te spelen; het emuleert de IPL. "
                "Als je de echte boot-animatie wilt, ga naar Config → GameCube/Wii → IPL en wijs het BIOS-bestand aan."
            ),
        },
    ],
    "nethersx2": [
        {
            "question": "Is NetherSX2 legaal?",
            "answer": (
                "NetherSX2 is een patch op de open-source AetherSX2-code. "
                "De emulator zelf is legaal; je hebt echter je eigen PS2-BIOS nodig, "
                "verkregen van een PS2 die je bezit."
            ),
        },
        {
            "question": "Welk BIOS heb ik nodig voor NetherSX2?",
            "answer": (
                "Je hebt een PS2-BIOS nodig (bijv. SCPH-70012.bin voor PS2 Slim). "
                "Plaats het in /NetherSX2/bios/ of het pad dat in Settings → BIOS is ingesteld."
            ),
        },
        {
            "question": "Games starten niet in NetherSX2 — wat nu?",
            "answer": (
                "1. Controleer of het BIOS correct is geconfigureerd. "
                "2. Probeer een ander ISO-formaat (CHD heeft de voorkeur). "
                "3. Schakel de 'Fast Boot' optie uit in System Settings. "
                "4. Zorg dat je ROM niet beschadigd is via CRC-check."
            ),
        },
    ],
    "lime3ds": [
        {
            "question": "Heb ik een 3DS-firmware nodig voor Lime3DS?",
            "answer": (
                "De meeste games werken zonder firmware. "
                "Voor games die AES-sleutels vereisen (bijv. bepaalde DLC of encrypted games), "
                "heb je 'aes_keys.txt' nodig van een gehackte 3DS."
            ),
        },
        {
            "question": "Wat is het verschil tussen Lime3DS en Citra?",
            "answer": (
                "Lime3DS is een fork van Citra die actief wordt bijgehouden nadat Citra gestopt is. "
                "Lime3DS bevat prestatieverbeteringen en bugfixes die niet in de officiële Citra-build zitten."
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Hotkey help (NL & EN)
# ---------------------------------------------------------------------------

HOTKEY_HELP: dict[str, dict[str, Any]] = {
    "retroarch_rgc": {
        "standard": "Retro Game Corps (RGC)",
        "hotkey_button": "SELECT",
        "description": {
            "nl": "De RGC-standaard gebruikt SELECT als hotkey-knop.",
            "en": "The RGC standard uses SELECT as the hotkey trigger button.",
        },
        "bindings": {
            "SELECT + START": {"nl": "RetroArch sluiten", "en": "Close RetroArch"},
            "SELECT + A": {"nl": "Reset game", "en": "Reset game"},
            "SELECT + B": {"nl": "RetroArch menu", "en": "RetroArch menu"},
            "SELECT + X": {"nl": "Quick Menu", "en": "Quick Menu"},
            "SELECT + Y": {"nl": "Mute audio", "en": "Mute audio"},
            "SELECT + R1": {"nl": "Save state opslaan", "en": "Save state"},
            "SELECT + L1": {"nl": "Save state laden", "en": "Load state"},
            "SELECT + R2": {"nl": "Snelheid verhogen", "en": "Fast forward"},
            "SELECT + L2": {"nl": "Vorig state-slot", "en": "Previous state slot"},
            "SELECT + UP": {"nl": "Volume omhoog", "en": "Volume up"},
            "SELECT + DOWN": {"nl": "Volume omlaag", "en": "Volume down"},
            "SELECT + LEFT": {"nl": "Vorig state-slot", "en": "Previous state slot"},
            "SELECT + RIGHT": {"nl": "Volgend state-slot", "en": "Next state slot"},
        },
    },
    "retroarch_techdweeb": {
        "standard": "TechDweeb",
        "hotkey_button": "MENU / Home",
        "description": {
            "nl": "TechDweeb gebruikt de MENU- of Home-knop als hotkey.",
            "en": "TechDweeb uses the MENU or Home button as the hotkey trigger.",
        },
        "bindings": {
            "MENU + START": {"nl": "RetroArch sluiten", "en": "Close RetroArch"},
            "MENU + SELECT": {"nl": "Quick Menu", "en": "Quick Menu"},
            "MENU + R1": {"nl": "Save state opslaan", "en": "Save state"},
            "MENU + L1": {"nl": "Save state laden", "en": "Load state"},
            "MENU + R2": {"nl": "Snelheid verhogen", "en": "Fast forward"},
            "MENU + L2": {"nl": "Pauzeren / hervatten", "en": "Pause / resume"},
            "MENU + A": {"nl": "Reset game", "en": "Reset game"},
            "MENU + UP": {"nl": "Volume omhoog", "en": "Volume up"},
            "MENU + DOWN": {"nl": "Volume omlaag", "en": "Volume down"},
            "MENU + RIGHT": {"nl": "Volgend state-slot", "en": "Next state slot"},
            "MENU + LEFT": {"nl": "Vorig state-slot", "en": "Previous state slot"},
        },
    },
    "ppsspp": {
        "standard": "PPSSPP Default",
        "description": {
            "nl": "PPSSPP hotkeys worden ingesteld via Instellingen → Systeem → Sneltoetsen.",
            "en": "PPSSPP hotkeys are configured via Settings → System → Key mappings.",
        },
        "bindings": {
            "Hold Home": {"nl": "PPSSPP-menu openen", "en": "Open PPSSPP menu"},
            "Back button": {"nl": "Vorige pagina / menu sluiten", "en": "Go back / close menu"},
        },
    },
    "dolphin": {
        "standard": "Dolphin Default",
        "description": {
            "nl": "Dolphin Android heeft een zwevende knopbalk voor snelle toegang.",
            "en": "Dolphin Android uses a floating overlay button for quick access.",
        },
        "bindings": {
            "Overlay button": {"nl": "Dolphin menu openen", "en": "Open Dolphin menu"},
            "Volume buttons": {"nl": "Kunnen worden gemapped als knoppen", "en": "Can be mapped as buttons"},
        },
    },
}

# ---------------------------------------------------------------------------
# BIOS help
# ---------------------------------------------------------------------------

BIOS_HELP: dict[str, dict[str, Any]] = {
    "ps1": {
        "display_name": "PlayStation 1",
        "required_files": ["scph5500.bin", "scph5501.bin", "scph5502.bin", "scph1001.bin"],
        "location": {
            "retroarch": "RetroArch/system/",
            "standalone": "N/A — PS1 emulation via RetroArch (Beetle PSX / PCSX ReARMed)",
        },
        "notes": {
            "nl": (
                "Gebruik bij voorkeur SCPH5501 (NTSC-U). "
                "Controleer de MD5-hash om te verifiëren dat het BIOS geldig is. "
                "Beetle PSX HW vereist BIOS; PCSX ReARMed kan zonder."
            ),
            "en": (
                "Prefer SCPH5501 (NTSC-U). Verify with MD5 checksum. "
                "Beetle PSX HW requires BIOS; PCSX ReARMed can run without."
            ),
        },
        "troubleshooting": [
            "Controleer hoofdlettergevoeligheid van bestandsnamen.",
            "Verifieer MD5/SHA1 hash met een tool als HashCheck.",
            "Zorg dat het bestand niet .zip of .7z is — pakkeer het uit.",
        ],
    },
    "ps2": {
        "display_name": "PlayStation 2",
        "required_files": ["SCPH-70012.bin", "SCPH-39001.bin", "SCPH-30004R.bin"],
        "location": {
            "nethersx2": "NetherSX2/bios/",
        },
        "notes": {
            "nl": (
                "Je hebt het BIOS nodig van een PS2 die je bezit. "
                "SCPH-70012 (PS2 Slim) werkt goed met NetherSX2."
            ),
            "en": (
                "You must dump BIOS from a PS2 you own. "
                "SCPH-70012 (PS2 Slim) works well with NetherSX2."
            ),
        },
        "troubleshooting": [
            "Ga naar NetherSX2 Settings → BIOS en selecteer het juiste bestand.",
            "Controleer de bestandsnaam — geen kleine letters vereist maar houd het consistent.",
            "Sommige BIOS-versies zijn regio-gebonden; gebruik de juiste regio voor jouw games.",
        ],
    },
    "gba": {
        "display_name": "Game Boy Advance",
        "required_files": ["gba_bios.bin"],
        "location": {
            "retroarch": "RetroArch/system/",
        },
        "notes": {
            "nl": (
                "De meeste GBA-cores werken zonder BIOS. "
                "Het officiële BIOS verbetert compatibiliteit bij introbios-games. "
                "MD5: a860e8c0b6d573d191e4ec7db1b1e4f6"
            ),
            "en": (
                "Most GBA cores run without BIOS. "
                "Official BIOS improves compatibility for intro-dependent games. "
                "MD5: a860e8c0b6d573d191e4ec7db1b1e4f6"
            ),
        },
        "troubleshooting": [
            "Bestandsnaam moet exact 'gba_bios.bin' zijn (kleine letters).",
            "Gebruik mGBA-core voor de beste GBA-compatibiliteit.",
        ],
    },
    "ds": {
        "display_name": "Nintendo DS",
        "required_files": ["bios7.bin", "bios9.bin", "firmware.bin"],
        "location": {
            "retroarch": "RetroArch/system/",
            "melonds": "melonDS/bios/",
        },
        "notes": {
            "nl": (
                "DraStic (betaald) werkt zonder BIOS. "
                "melonDS en de melonDS RetroArch-core vereisen BIOS voor sommige features."
            ),
            "en": (
                "DraStic (paid) works without BIOS. "
                "melonDS and the melonDS RetroArch core require BIOS for some features."
            ),
        },
        "troubleshooting": [
            "Dumb alle drie de bestanden; een ontbrekend bestand geeft problemen.",
            "Zorg dat firmware.bin van een ongemodificeerde DS komt voor optimale compatibiliteit.",
        ],
    },
    "3ds": {
        "display_name": "Nintendo 3DS",
        "required_files": ["aes_keys.txt"],
        "location": {
            "lime3ds": "Lime3DS/sysdata/",
            "citra": "Citra/sysdata/",
        },
        "notes": {
            "nl": (
                "Lime3DS vereist geen volledige firmware voor de meeste games. "
                "Encrypted games en DLC vereisen AES-sleutels van een eigen gehackte 3DS."
            ),
            "en": (
                "Lime3DS does not require full firmware for most games. "
                "Encrypted games and DLC require AES keys dumped from your own hacked 3DS."
            ),
        },
        "troubleshooting": [
            "Gebruik GodMode9 op een gehackte 3DS om sleutels te dumpen.",
            "Controleer of het bestand de correcte sleutelindeling heeft.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Knowledge base class
# ---------------------------------------------------------------------------


class KnowledgeBase:
    """Provides keyword-based search over EmuFlow's static knowledge."""

    def __init__(self) -> None:
        self._documents = self._build_index()

    def _build_index(self) -> list[tuple[set[str], str]]:
        """Build a flat list of (keyword_set, text) tuples for fast matching."""
        docs: list[tuple[set[str], str]] = []

        # Known issues
        for issue_id, issue in KNOWN_ISSUES.items():
            text = (
                f"[Issue: {issue_id}] "
                f"Problem: {issue['problem']} "
                f"Solution: {issue['solution']}"
            )
            keywords = self._extract_keywords(issue_id + " " + issue["problem"])
            docs.append((keywords, text))

        # FAQs
        for emulator, faqs in EMULATOR_FAQS.items():
            for faq in faqs:
                text = (
                    f"[FAQ: {emulator}] "
                    f"Q: {faq['question']} "
                    f"A: {faq['answer']}"
                )
                keywords = self._extract_keywords(emulator + " " + faq["question"])
                docs.append((keywords, text))

        # Hotkeys
        for standard_id, hotkey_data in HOTKEY_HELP.items():
            nl_desc = hotkey_data["description"].get("nl", "")
            en_desc = hotkey_data["description"].get("en", "")
            bindings_text = " ".join(
                f"{combo}: {labels.get('nl', '')} / {labels.get('en', '')}"
                for combo, labels in hotkey_data.get("bindings", {}).items()
            )
            text = (
                f"[Hotkeys: {standard_id}] "
                f"{nl_desc} {en_desc} "
                f"Bindings: {bindings_text}"
            )
            keywords = self._extract_keywords(standard_id + " hotkey " + nl_desc)
            docs.append((keywords, text))

        # BIOS
        for system_id, bios_data in BIOS_HELP.items():
            nl_notes = bios_data["notes"].get("nl", "")
            files = " ".join(bios_data.get("required_files", []))
            troubleshooting = " ".join(bios_data.get("troubleshooting", []))
            text = (
                f"[BIOS: {bios_data['display_name']}] "
                f"Files: {files} "
                f"Notes: {nl_notes} "
                f"Troubleshooting: {troubleshooting}"
            )
            keywords = self._extract_keywords(system_id + " " + bios_data["display_name"] + " bios")
            docs.append((keywords, text))

        return docs

    @staticmethod
    def _extract_keywords(text: str) -> set[str]:
        """Lowercase, strip punctuation, return word set."""
        cleaned = re.sub(r"[^a-zA-Z0-9\s\-]", " ", text.lower())
        return set(cleaned.split())

    def search(self, query: str) -> list[str]:
        """Search for knowledge base entries relevant to *query*.

        Uses simple keyword overlap scoring. Returns up to 5 matching
        document strings, sorted by descending relevance.

        Args:
            query: Natural language query.

        Returns:
            List of matching document strings (may be empty).
        """
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return []

        scored: list[tuple[int, str]] = []
        for doc_keywords, doc_text in self._documents:
            overlap = len(query_keywords & doc_keywords)
            if overlap > 0:
                scored.append((overlap, doc_text))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:5]]
