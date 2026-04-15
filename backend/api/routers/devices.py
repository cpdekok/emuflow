"""
EmuFlow API — Devices Router
Handles Android device registration and hardware profile retrieval.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.hardware.profiler import HardwareProfiler

router = APIRouter()
profiler = HardwareProfiler()

# ---------------------------------------------------------------------------
# In-memory device store (MVP)
# ---------------------------------------------------------------------------
_devices: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class DeviceRegisterRequest(BaseModel):
    """Payload for registering a new Android device."""

    device_name: str = Field(..., description="Human-readable device name, e.g. 'Redmi Note 12'")
    chipset: str = Field(..., description="SoC model string, e.g. 'Snapdragon 4 Gen 2'")
    android_api: int = Field(..., ge=21, description="Android API level, e.g. 33")
    ram_gb: float = Field(..., gt=0, description="Total RAM in gigabytes")
    shizuku_available: bool = Field(False, description="Whether Shizuku is available on the device")


class DeviceResponse(BaseModel):
    """Serialised device record returned to the client."""

    device_id: str
    device_name: str
    chipset: str
    android_api: int
    ram_gb: float
    shizuku_available: bool
    detected_chipset_id: Optional[str] = None


class DeviceProfileResponse(BaseModel):
    """Full hardware profile including optimal emulation settings."""

    device_id: str
    device_name: str
    chipset: str
    android_api: int
    ram_gb: float
    shizuku_available: bool
    chipset_id: str
    renderer: dict[str, str]
    recommended_emulators: dict[str, dict]
    performance_tier: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/register", response_model=DeviceResponse, status_code=201)
async def register_device(payload: DeviceRegisterRequest) -> DeviceResponse:
    """
    Register an Android device and store its hardware information.

    Returns the created device record including a generated device_id.
    """
    device_id = str(uuid.uuid4())

    build_info = {
        "hardware": payload.chipset,
        "soc_model": payload.chipset,
    }
    detected_chipset_id = profiler.detect_chipset_from_build_info(build_info)

    record = {
        "device_id": device_id,
        "device_name": payload.device_name,
        "chipset": payload.chipset,
        "android_api": payload.android_api,
        "ram_gb": payload.ram_gb,
        "shizuku_available": payload.shizuku_available,
        "detected_chipset_id": detected_chipset_id,
    }
    _devices[device_id] = record
    return DeviceResponse(**record)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str) -> DeviceResponse:
    """Retrieve stored information for a specific device by its ID."""
    if device_id not in _devices:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return DeviceResponse(**_devices[device_id])


@router.get("/{device_id}/profile", response_model=DeviceProfileResponse)
async def get_device_profile(device_id: str) -> DeviceProfileResponse:
    """
    Return the full hardware profile for a device, including optimal
    emulation-engine recommendations per gaming system.
    """
    if device_id not in _devices:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    dev = _devices[device_id]
    chipset_id = dev.get("detected_chipset_id") or "generic"

    # Build per-system emulator recommendations
    systems = ["nes", "snes", "gba", "psp", "ps1", "ps2", "nds", "gc", "wii", "3ds", "switch"]
    recommended: dict[str, dict] = {}
    for system in systems:
        use_standalone, package = profiler.should_use_standalone(system, dev["android_api"])
        renderer = profiler.select_renderer(chipset_id, system)
        optimal = profiler.get_optimal_profile(chipset_id, system)
        recommended[system] = {
            "use_standalone": use_standalone,
            "package": package,
            "renderer": renderer,
            "settings": optimal,
        }

    # Determine renderer per "tier"
    renderer_map = {
        s: profiler.select_renderer(chipset_id, s) for s in systems
    }

    # Simple performance tier based on RAM
    ram = dev["ram_gb"]
    if ram >= 12:
        tier = "high"
    elif ram >= 6:
        tier = "mid"
    else:
        tier = "low"

    return DeviceProfileResponse(
        device_id=device_id,
        device_name=dev["device_name"],
        chipset=dev["chipset"],
        android_api=dev["android_api"],
        ram_gb=dev["ram_gb"],
        shizuku_available=dev["shizuku_available"],
        chipset_id=chipset_id,
        renderer=renderer_map,
        recommended_emulators=recommended,
        performance_tier=tier,
    )
