"""
EmuFlow API — Controls Router
Manages controller layout profiles for various emulators and control standards.
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Built-in controller profiles
# ---------------------------------------------------------------------------

_PROFILES: dict[str, dict] = {
    "retroarch_rgc_standard": {
        "emulator": "retroarch",
        "standard": "rgc",
        "description": "RetroArch layout following RetroGameCorps standard",
        "mappings": {
            "a": "Cross / A",
            "b": "Circle / B",
            "x": "Square / X",
            "y": "Triangle / Y",
            "start": "Start",
            "select": "Select",
            "l1": "L1",
            "r1": "R1",
            "l2": "L2",
            "r2": "R2",
            "l3": "L3",
            "r3": "R3",
            "dpad_up": "D-Pad Up",
            "dpad_down": "D-Pad Down",
            "dpad_left": "D-Pad Left",
            "dpad_right": "D-Pad Right",
        },
        "hotkeys": {
            "menu": "Select + Start",
            "save_state": "Select + R1",
            "load_state": "Select + L1",
            "fast_forward": "Select + R2",
            "rewind": "Select + L2",
            "screenshot": "Select + X",
            "close_content": "Select + B",
        },
    },
    "retroarch_techdweeb": {
        "emulator": "retroarch",
        "standard": "techdweeb",
        "description": "RetroArch layout following TechDweeb / ETA Prime standard",
        "mappings": {
            "a": "A / East",
            "b": "B / South",
            "x": "X / North",
            "y": "Y / West",
            "start": "Menu",
            "select": "View / Back",
            "l1": "LB",
            "r1": "RB",
            "l2": "LT",
            "r2": "RT",
            "l3": "LS",
            "r3": "RS",
        },
        "hotkeys": {
            "menu": "View + Menu",
            "save_state": "View + RB",
            "load_state": "View + LB",
            "fast_forward": "View + RT",
            "rewind": "View + LT",
            "screenshot": "View + X",
            "close_content": "View + B",
        },
    },
    "ppsspp_standard": {
        "emulator": "ppsspp",
        "standard": "ppsspp",
        "description": "Default PPSSPP controller profile",
        "mappings": {
            "cross": "A",
            "circle": "B",
            "square": "X",
            "triangle": "Y",
            "start": "Start",
            "select": "Select",
            "l": "L1 / LB",
            "r": "R1 / RB",
            "analog_up": "Left Stick Up",
            "analog_down": "Left Stick Down",
            "analog_left": "Left Stick Left",
            "analog_right": "Left Stick Right",
        },
        "hotkeys": {
            "pause": "Start",
            "save_state": "L + R + Start",
            "load_state": "L + R + Select",
            "fast_forward": "R + Start",
            "screenshot": "L + R + Square",
        },
    },
    "dolphin_standard": {
        "emulator": "dolphin",
        "standard": "dolphin",
        "description": "Dolphin GC/Wii standard controller profile",
        "mappings": {
            "a": "A",
            "b": "B",
            "x": "X",
            "y": "Y",
            "z": "RB / R1",
            "start": "Start",
            "l": "LT / L2",
            "r": "RT / R2",
            "dpad_up": "D-Pad Up",
            "dpad_down": "D-Pad Down",
            "dpad_left": "D-Pad Left",
            "dpad_right": "D-Pad Right",
            "c_up": "Right Stick Up",
            "c_down": "Right Stick Down",
            "c_left": "Right Stick Left",
            "c_right": "Right Stick Right",
        },
        "hotkeys": {
            "pause": "Start + Select",
            "save_state": "Start + L",
            "load_state": "Start + R",
            "full_screen": "Start + Z",
        },
    },
    "drastic_standard": {
        "emulator": "drastic",
        "standard": "drastic",
        "description": "DraStic NDS standard controller profile",
        "mappings": {
            "a": "A",
            "b": "B",
            "x": "X",
            "y": "Y",
            "start": "Start",
            "select": "Select",
            "l": "L",
            "r": "R",
            "dpad_up": "D-Pad Up",
            "dpad_down": "D-Pad Down",
            "dpad_left": "D-Pad Left",
            "dpad_right": "D-Pad Right",
        },
        "hotkeys": {
            "menu": "Select + Start",
            "swap_screens": "Select + L",
            "screenshot": "Select + R",
            "fast_forward": "R + Start",
        },
    },
}

# ---------------------------------------------------------------------------
# Hotkey standards
# ---------------------------------------------------------------------------

_HOTKEYS: dict[str, dict] = {
    "rgc": {
        "description": "RetroGameCorps hotkey standard",
        "hotkeys": {
            "menu_toggle": "Select + Start",
            "save_state": "Select + R1",
            "load_state": "Select + L1",
            "fast_forward": "Select + R2",
            "rewind": "Select + L2",
            "screenshot": "Select + X",
            "close_content": "Select + B",
            "volume_up": "Select + D-Pad Up",
            "volume_down": "Select + D-Pad Down",
            "brightness_up": "Select + D-Pad Right",
            "brightness_down": "Select + D-Pad Left",
        },
    },
    "techdweeb": {
        "description": "TechDweeb / ETA Prime hotkey standard",
        "hotkeys": {
            "menu_toggle": "View + Menu",
            "save_state": "View + RB",
            "load_state": "View + LB",
            "fast_forward": "View + RT",
            "rewind": "View + LT",
            "screenshot": "View + X",
            "close_content": "View + B",
            "next_state_slot": "View + D-Pad Right",
            "prev_state_slot": "View + D-Pad Left",
        },
    },
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ApplyControlRequest(BaseModel):
    """Request to apply a controller profile to a specific emulator on a device."""

    device_id: str
    emulator: str
    profile_name: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_config_payload(emulator: str, profile: dict) -> str:
    """Generate a simple text config snippet from a profile dict."""
    lines = [f"# EmuFlow generated config for {emulator}"]
    lines.append(f"# Profile: {profile.get('description', 'N/A')}")
    lines.append("")
    lines.append("[mappings]")
    for btn, target in profile.get("mappings", {}).items():
        lines.append(f"{btn} = {target}")
    lines.append("")
    lines.append("[hotkeys]")
    for action, combo in profile.get("hotkeys", {}).items():
        lines.append(f"{action} = {combo}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/profiles", summary="List available controller profiles")
async def list_profiles() -> dict:
    """Return a summary list of all built-in controller profiles."""
    summary = {
        name: {
            "emulator": p["emulator"],
            "standard": p["standard"],
            "description": p["description"],
        }
        for name, p in _PROFILES.items()
    }
    return {"profiles": summary, "count": len(summary)}


@router.get("/profiles/{profile_name}", summary="Get a specific controller profile")
async def get_profile(profile_name: str) -> dict:
    """
    Return the full controller profile for the given profile name.

    Available profiles: retroarch_rgc_standard, retroarch_techdweeb,
    ppsspp_standard, dolphin_standard, drastic_standard.
    """
    if profile_name not in _PROFILES:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_name}' not found. "
                   f"Available: {list(_PROFILES.keys())}",
        )
    return {"profile_name": profile_name, "profile": _PROFILES[profile_name]}


@router.post("/apply", summary="Apply a controller profile to an emulator")
async def apply_profile(payload: ApplyControlRequest) -> dict:
    """
    Generate and return a config payload string for a given device, emulator,
    and controller profile combination.
    """
    if payload.profile_name not in _PROFILES:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{payload.profile_name}' not found",
        )

    profile = _PROFILES[payload.profile_name]
    if profile["emulator"] != payload.emulator:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Profile '{payload.profile_name}' is for emulator "
                f"'{profile['emulator']}', not '{payload.emulator}'"
            ),
        )

    config = _generate_config_payload(payload.emulator, profile)
    return {
        "device_id": payload.device_id,
        "emulator": payload.emulator,
        "profile_name": payload.profile_name,
        "config_payload": config,
    }


@router.get("/hotkeys/{standard}", summary="Get hotkey mapping for a control standard")
async def get_hotkeys(standard: str) -> dict:
    """
    Return the hotkey mapping for either the 'rgc' or 'techdweeb' standard.
    """
    if standard not in _HOTKEYS:
        raise HTTPException(
            status_code=404,
            detail=f"Standard '{standard}' not found. Available: {list(_HOTKEYS.keys())}",
        )
    return {"standard": standard, **_HOTKEYS[standard]}
