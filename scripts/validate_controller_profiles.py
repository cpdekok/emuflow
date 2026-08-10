#!/usr/bin/env python3
"""
EmuFlow — Controller Profielen Validatie Script
Valideert de controller-profielen in config/controller_profiles/ op geldigheid:
- JSON-profielen moeten geldige JSON zijn en een 'metadata' blok bevatten.
- .ini/.cfg-profielen moeten bestaan en niet leeg zijn.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROFILES_DIR = ROOT / "config" / "controller_profiles"

TEXT_CONFIG_SUFFIXES = {".ini", ".cfg"}

errors = []
warnings = []


def validate_json_profile(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"[SYNTAX ERROR] {path.relative_to(ROOT)}: {e}")
        return
    if not isinstance(data, dict):
        errors.append(f"[STRUCTURE ERROR] {path.relative_to(ROOT)}: root moet een object zijn")
        return
    if "metadata" not in data:
        errors.append(f"[MISSING FIELD] {path.relative_to(ROOT)}: ontbreekt 'metadata'")


def validate_text_profile(path: Path):
    content = path.read_text(encoding="utf-8", errors="replace").strip()
    if not content:
        errors.append(f"[EMPTY] {path.relative_to(ROOT)}: bestand is leeg")


def main():
    print("EmuFlow Controller Profielen Validatie")
    print("=" * 50)

    if not PROFILES_DIR.exists():
        errors.append("[MISSING DIR] config/controller_profiles/ niet gevonden")
    else:
        profiles = sorted(p for p in PROFILES_DIR.rglob("*") if p.is_file())
        if not profiles:
            warnings.append("[WARN] geen controller-profielen gevonden in config/controller_profiles/")
        for path in profiles:
            suffix = path.suffix.lower()
            if suffix == ".json":
                validate_json_profile(path)
            elif suffix in TEXT_CONFIG_SUFFIXES:
                validate_text_profile(path)
            else:
                warnings.append(f"[WARN] {path.relative_to(ROOT)}: onbekend profielformaat '{suffix}', overgeslagen")
                continue
            print(f"  ✓ {path.relative_to(PROFILES_DIR)} gecontroleerd")

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
        print(f"  Alle controller-profielen geldig. ({len(warnings)} waarschuwing(en))")
        sys.exit(0)


if __name__ == "__main__":
    main()
