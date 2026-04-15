#!/usr/bin/env python3
"""
EmuFlow — Config Validatie Script
Valideert alle JSON configuratiebestanden op geldigheid en volledigheid.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_DIR = ROOT / "config"

REQUIRED_CHIPSET_FIELDS = ["chipset_id", "chipset_display", "gpu_family", "vulkan_support", "ram_gb_typical", "emulation_profiles"]
REQUIRED_HOTKEY_FIELDS  = ["metadata", "hotkeys", "recommended_settings"]
REQUIRED_HOTKEYS        = ["hotkey_enable", "save_state", "load_state", "fast_forward", "quit"]

errors = []
warnings = []


def validate_json_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"[SYNTAX ERROR] {path.relative_to(ROOT)}: {e}")
        return None


def validate_chipsets(path: Path):
    data = validate_json_file(path)
    if not data:
        return
    chipsets = data if isinstance(data, list) else [data]
    for chip in chipsets:
        for field in REQUIRED_CHIPSET_FIELDS:
            if field not in chip:
                errors.append(f"[MISSING FIELD] {path.name} / {chip.get('chipset_id', '?')}: ontbreekt '{field}'")
        if "emulation_profiles" in chip and not chip["emulation_profiles"]:
            warnings.append(f"[WARN] {chip.get('chipset_id', '?')}: emulation_profiles is leeg")


def validate_hotkey_standard(path: Path):
    data = validate_json_file(path)
    if not data:
        return
    for field in REQUIRED_HOTKEY_FIELDS:
        if field not in data:
            errors.append(f"[MISSING FIELD] {path.name}: ontbreekt '{field}'")
    hotkeys = data.get("hotkeys", {})
    for key in REQUIRED_HOTKEYS:
        if key not in hotkeys:
            warnings.append(f"[WARN] {path.name}: hotkey '{key}' niet gedefinieerd")


def main():
    print("EmuFlow Config Validatie")
    print("=" * 50)

    # Chipset profielen
    chipsets_file = CONFIG_DIR / "hardware_profiles" / "chipsets.json"
    if chipsets_file.exists():
        validate_chipsets(chipsets_file)
        print(f"  ✓ chipsets.json gecontroleerd")
    else:
        errors.append(f"[MISSING FILE] config/hardware_profiles/chipsets.json niet gevonden")

    # Hotkey standards
    hotkey_dir = CONFIG_DIR / "hotkey_standards"
    for json_file in hotkey_dir.glob("*.json"):
        validate_hotkey_standard(json_file)
        print(f"  ✓ {json_file.name} gecontroleerd")

    # Alle andere JSON bestanden in config/
    for json_file in CONFIG_DIR.rglob("*.json"):
        if json_file not in [chipsets_file] and "hotkey_standards" not in str(json_file):
            data = validate_json_file(json_file)
            if data is not None:
                print(f"  ✓ {json_file.relative_to(CONFIG_DIR)} gecontroleerd")

    print("\n" + "=" * 50)
    if warnings:
        for w in warnings:
            print(f"  ⚠ {w}")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n{len(errors)} fout(en) gevonden. CI mislukt.")
        sys.exit(1)
    else:
        print(f"  Alle configs geldig. ({len(warnings)} waarschuwing(en))")
        sys.exit(0)


if __name__ == "__main__":
    main()
