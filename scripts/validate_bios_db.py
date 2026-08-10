#!/usr/bin/env python3
"""
EmuFlow — BIOS Hash Database Validatie Script
Valideert de ingebouwde BIOS hash database (backend/core/bios/checker.py) op
volledigheid en correcte MD5-hashformaten.
"""

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHECKER_PATH = ROOT / "backend" / "core" / "bios" / "checker.py"

MD5_RE = re.compile(r"^[0-9a-f]{32}$")
REQUIRED_ENTRY_FIELDS = ["filename", "system", "md5", "required"]

errors = []
warnings = []


def load_bios_hashes() -> dict | None:
    if not CHECKER_PATH.exists():
        errors.append(f"[MISSING FILE] {CHECKER_PATH.relative_to(ROOT)} niet gevonden")
        return None
    spec = importlib.util.spec_from_file_location("emuflow_bios_checker", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:  # noqa: BLE001
        errors.append(f"[IMPORT ERROR] {CHECKER_PATH.name}: {e}")
        return None
    checker = getattr(module, "BIOSChecker", None)
    if checker is None or not hasattr(checker, "BIOS_HASHES"):
        errors.append(f"[STRUCTURE ERROR] {CHECKER_PATH.name}: BIOSChecker.BIOS_HASHES ontbreekt")
        return None
    return checker.BIOS_HASHES


def validate_bios_db():
    hashes = load_bios_hashes()
    if hashes is None:
        return

    if not hashes:
        errors.append("[EMPTY] BIOS_HASHES database is leeg")
        return

    for key, entry in hashes.items():
        label = f"BIOS '{key}'"

        for field in REQUIRED_ENTRY_FIELDS:
            if not hasattr(entry, field):
                errors.append(f"[MISSING FIELD] {label}: ontbreekt '{field}'")

        filename = getattr(entry, "filename", "")
        system = getattr(entry, "system", "")
        md5 = getattr(entry, "md5", "")
        required = getattr(entry, "required", None)

        if not filename:
            errors.append(f"[MISSING FIELD] {label}: 'filename' is leeg")
        if not system:
            errors.append(f"[MISSING FIELD] {label}: 'system' is leeg")

        if not isinstance(md5, str):
            errors.append(f"[BAD HASH] {label}: md5 moet een string zijn (nu: {type(md5).__name__})")
        elif md5 == "":
            # Sommige BIOS-bestanden (bv. NDS firmware.bin, PS2 per-model dumps) hebben
            # geen enkele canonieke MD5. Lege hash is toegestaan, maar wordt gemeld.
            warnings.append(f"[WARN] {label}: geen MD5-hash gedefinieerd (console-/regio-specifiek?)")
        elif not MD5_RE.match(md5.lower()):
            errors.append(f"[BAD HASH] {label}: md5 '{md5}' is geen geldige 32-tekens hex hash")

        if not isinstance(required, bool):
            errors.append(f"[BAD TYPE] {label}: 'required' moet een boolean zijn (nu: {type(required).__name__})")

        if isinstance(filename, str) and filename and key != filename.lower():
            warnings.append(f"[WARN] {label}: database-sleutel komt niet overeen met filename.lower() ('{filename.lower()}')")


def main():
    print("EmuFlow BIOS Hash Database Validatie")
    print("=" * 50)

    validate_bios_db()
    print("  ✓ backend/core/bios/checker.py gecontroleerd")

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
        print(f"  BIOS database geldig. ({len(warnings)} waarschuwing(en))")
        sys.exit(0)


if __name__ == "__main__":
    main()
