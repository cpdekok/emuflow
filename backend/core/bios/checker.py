"""
EmuFlow — BIOS Checker
Validates BIOS file MD5 hashes against a known-good database.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger("emuflow.bios_checker")


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class BIOSCheckResult(Enum):
    """Result of a single BIOS file hash comparison."""

    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BIOSEntry:
    """Metadata for a single known BIOS file."""

    filename: str
    system: str
    md5: str
    required: bool
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# BIOSChecker
# ---------------------------------------------------------------------------

class BIOSChecker:
    """
    Validates BIOS file MD5 hashes against a built-in known-good database.

    The database covers:
    - PS1 (scph1001.bin)
    - Dreamcast (dc_boot.bin, dc_flash.bin)
    - Nintendo DS (bios7.bin, bios9.bin, firmware.bin)
    - Game Boy Advance (gba_bios.bin)
    """

    # ------------------------------------------------------------------
    # Known-good BIOS hash database
    # Keys are lowercase filenames for case-insensitive lookup.
    # ------------------------------------------------------------------

    BIOS_HASHES: dict[str, BIOSEntry] = {
        # ---------------------------------------------------------------
        # PlayStation 1
        # ---------------------------------------------------------------
        "scph1001.bin": BIOSEntry(
            filename="scph1001.bin",
            system="ps1",
            md5="924e392ed05558ffdb115408c263dccf",
            required=True,
            notes="PS1 BIOS v2.2 (USA) — most compatible version for PCSX-ReARMed",
        ),
        "scph5500.bin": BIOSEntry(
            filename="scph5500.bin",
            system="ps1",
            md5="8dd7d5296a650fac7319bce665a6a53c",
            required=False,
            notes="PS1 BIOS v3.0 (Japan)",
        ),
        "scph5501.bin": BIOSEntry(
            filename="scph5501.bin",
            system="ps1",
            md5="490f666e1afb15b7362b406ed1cea246",
            required=False,
            notes="PS1 BIOS v3.0 (USA)",
        ),
        "scph5502.bin": BIOSEntry(
            filename="scph5502.bin",
            system="ps1",
            md5="32736f17079d0b2b7024407c39bd3050",
            required=False,
            notes="PS1 BIOS v3.0 (Europe)",
        ),
        "scph7001.bin": BIOSEntry(
            filename="scph7001.bin",
            system="ps1",
            md5="1e68c231d0896b7eadcad1d7d8e76129",
            required=False,
            notes="PS1 BIOS v4.1 (USA)",
        ),
        # ---------------------------------------------------------------
        # Sega Dreamcast
        # ---------------------------------------------------------------
        "dc_boot.bin": BIOSEntry(
            filename="dc_boot.bin",
            system="dreamcast",
            md5="e10c53c2f8b90bab96ead2d368858623",
            required=True,
            notes="Dreamcast BIOS — required for Flycast/Redream",
        ),
        "dc_flash.bin": BIOSEntry(
            filename="dc_flash.bin",
            system="dreamcast",
            md5="0a93f7940c455905bea79785b78edd6b",
            required=True,
            notes="Dreamcast flash ROM — required alongside dc_boot.bin",
        ),
        # ---------------------------------------------------------------
        # Nintendo DS
        # ---------------------------------------------------------------
        "bios7.bin": BIOSEntry(
            filename="bios7.bin",
            system="nds",
            md5="df692a80a5b1bc90728bc3dfc76cd948",
            required=True,
            notes="NDS ARM7 BIOS — required for melonDS/melonDS DS",
        ),
        "bios9.bin": BIOSEntry(
            filename="bios9.bin",
            system="nds",
            md5="a392174eb3e572fed6447e956bde4b25",
            required=True,
            notes="NDS ARM9 BIOS — required for melonDS/melonDS DS",
        ),
        "firmware.bin": BIOSEntry(
            filename="firmware.bin",
            system="nds",
            md5="",  # Varies by console firmware version; checked as unknown
            required=False,
            notes=(
                "NDS firmware — MD5 varies by console; presence is sufficient. "
                "Will always return 'unknown' from hash check."
            ),
        ),
        # ---------------------------------------------------------------
        # Game Boy Advance
        # ---------------------------------------------------------------
        "gba_bios.bin": BIOSEntry(
            filename="gba_bios.bin",
            system="gba",
            md5="a860e8c0b6d573d191e4ec7db1b1e4f6",
            required=False,
            notes=(
                "Official GBA BIOS — optional for mGBA (HLE BIOS used otherwise). "
                "Required for accurate timing in some games."
            ),
        ),
        # ---------------------------------------------------------------
        # PlayStation 2
        # ---------------------------------------------------------------
        "ps2-0160e-20001027.bin": BIOSEntry(
            filename="ps2-0160e-20001027.bin",
            system="ps2",
            md5="",
            required=True,
            notes=(
                "PS2 BIOS (Europe, v1.60) — exact MD5 varies by dump; "
                "NetherSX2 requires a valid PS2 BIOS dump."
            ),
        ),
        "ps2-0200a-20040614.bin": BIOSEntry(
            filename="ps2-0200a-20040614.bin",
            system="ps2",
            md5="",
            required=False,
            notes="PS2 BIOS (USA, v2.00) — commonly used dump.",
        ),
        # ---------------------------------------------------------------
        # Sega Saturn
        # ---------------------------------------------------------------
        "sega_101.bin": BIOSEntry(
            filename="sega_101.bin",
            system="saturn",
            md5="224b8048d9755a744b74e5af9a5d66d0",
            required=True,
            notes="Sega Saturn BIOS v1.01 (Japan) — Yaba Sanshiro 2 / Kronos",
        ),
        "mpr-17933.bin": BIOSEntry(
            filename="mpr-17933.bin",
            system="saturn",
            md5="3240872c70984b6cbfda1586cab68dbe",
            required=False,
            notes="Sega Saturn BIOS (USA/Europe)",
        ),
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_file(self, filename: str, md5_hash: str) -> BIOSCheckResult:
        """
        Compare a BIOS file's MD5 hash against the known-good database.

        Args:
            filename:  Name of the BIOS file (case-insensitive).
            md5_hash:  MD5 hash string of the file to check.

        Returns:
            BIOSCheckResult.PASSED  — hash matches database entry.
            BIOSCheckResult.FAILED  — filename known but hash mismatches.
            BIOSCheckResult.UNKNOWN — filename not in database.
        """
        entry = self.BIOS_HASHES.get(filename.lower())

        if entry is None:
            logger.debug("BIOS file '%s' is not in the database (unknown)", filename)
            return BIOSCheckResult.UNKNOWN

        # Files whose stored MD5 is empty are inherently unknowable
        if not entry.md5:
            logger.debug(
                "BIOS file '%s' has no reference hash stored — returning unknown",
                filename,
            )
            return BIOSCheckResult.UNKNOWN

        if md5_hash.lower() == entry.md5.lower():
            logger.debug("BIOS file '%s' PASSED hash check", filename)
            return BIOSCheckResult.PASSED

        logger.warning(
            "BIOS file '%s' FAILED: expected %s, got %s",
            filename, entry.md5, md5_hash,
        )
        return BIOSCheckResult.FAILED

    def check_all(self, bios_list: list[dict]) -> dict[str, str]:
        """
        Validate a list of BIOS file entries.

        Args:
            bios_list: List of dicts each containing 'filename' and 'md5'.

        Returns:
            Dict mapping filename → result string ('passed'/'failed'/'unknown').
        """
        results: dict[str, str] = {}
        for item in bios_list:
            filename = item.get("filename", "")
            md5_hash = item.get("md5", "")
            result = self.check_file(filename, md5_hash)
            results[filename] = result.value
        return results

    def is_safe_to_link(self, filename: str, md5_hash: str) -> bool:
        """
        Determine whether it is safe to link to the BIOS download.

        A file is considered "safe to link" only when its hash is verified
        as PASSED. Unknown or failed files should not be linked.

        Args:
            filename:  BIOS file name (case-insensitive).
            md5_hash:  MD5 hash of the file.

        Returns:
            True only if the hash comparison returns PASSED.
        """
        return self.check_file(filename, md5_hash) == BIOSCheckResult.PASSED
