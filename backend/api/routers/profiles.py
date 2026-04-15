"""
EmuFlow API — Profiles Router
Serves hardware profiles for known Android chipsets.
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

logger = logging.getLogger("emuflow.profiles")
router = APIRouter()

# ---------------------------------------------------------------------------
# Path to chipset data
# ---------------------------------------------------------------------------
_CHIPSETS_PATH = Path("/home/user/workspace/emuflow/config/hardware_profiles/chipsets.json")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_chipsets() -> dict:
    """Load chipset profiles from JSON, falling back to an empty dict on error."""
    try:
        with open(_CHIPSETS_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        logger.warning("chipsets.json not found at %s — returning empty profile set", _CHIPSETS_PATH)
        return {}
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse chipsets.json: %s", exc)
        return {}
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error loading chipsets.json: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", summary="List all supported chipsets")
async def list_profiles() -> dict:
    """
    Return a list of all chipset IDs and their human-readable names.

    Data is loaded from chipsets.json; an empty list is returned if the file
    is unavailable.
    """
    chipsets = _load_chipsets()
    summary = {
        chip_id: {
            "name": data.get("name", chip_id),
            "manufacturer": data.get("manufacturer", "Unknown"),
            "tier": data.get("tier", "unknown"),
        }
        for chip_id, data in chipsets.items()
    }
    return {"chipsets": summary, "count": len(summary)}


@router.get("/{chipset_id}", summary="Get hardware profile for a specific chipset")
async def get_profile(chipset_id: str) -> dict:
    """
    Return the full hardware profile JSON for the requested chipset.

    Raises 404 if the chipset is not found in the database.
    """
    chipsets = _load_chipsets()
    if chipset_id not in chipsets:
        raise HTTPException(
            status_code=404,
            detail=f"Chipset '{chipset_id}' not found in profile database",
        )
    return {"chipset_id": chipset_id, "profile": chipsets[chipset_id]}
