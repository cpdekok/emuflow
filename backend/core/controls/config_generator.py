"""
EmuFlow - Controller Config Generator
Generates RetroArch, PPSSPP, and Dolphin configuration files for common
handheld Android gaming devices.
"""

from __future__ import annotations

import json
import logging
import os
import textwrap
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODULE_DIR = Path(__file__).parent
_CONFIG_ROOT = _MODULE_DIR.parent.parent.parent / "config"
_HOTKEY_STANDARDS_DIR = _CONFIG_ROOT / "hotkey_standards"

# ---------------------------------------------------------------------------
# Device profile data
# Defines A/B-swap and default layout notes for each supported device family.
# ---------------------------------------------------------------------------

DEVICE_PROFILES: dict[str, dict[str, Any]] = {
    "retroid": {
        "display_name": "Retroid Pocket",
        "layout": "nintendo",            # A=right, B=bottom (Nintendo)
        "swap_ab": False,                # No swap needed — RetroArch already defaults to Nintendo
        "swap_xy": False,
        "description": "Nintendo button layout (A right, B bottom). Standard RetroArch default.",
    },
    "odin": {
        "display_name": "Ayn Odin",
        "layout": "xbox",               # A=bottom, B=right (Xbox)
        "swap_ab": True,                # Swap needed for Nintendo-style games
        "swap_xy": True,
        "description": "Xbox layout (A bottom, B right). Swap A/B for Nintendo-style mapping.",
    },
    "anbernic": {
        "display_name": "Anbernic RG",
        "layout": "nintendo",
        "swap_ab": False,
        "swap_xy": False,
        "description": "Nintendo button layout, similar to Retroid Pocket.",
    },
    "ayaneo": {
        "display_name": "AyaNeo",
        "layout": "xbox",
        "swap_ab": True,
        "swap_xy": True,
        "description": "Xbox layout (A bottom, B right). Swap A/B recommended.",
    },
    "generic": {
        "display_name": "Generic Android Controller",
        "layout": "xbox",
        "swap_ab": False,
        "swap_xy": False,
        "description": "Generic Xbox-style controller; no overrides applied.",
    },
}

# ---------------------------------------------------------------------------
# Embedded hotkey definitions
# (Used as fallback when JSON files are not present on disk.)
# ---------------------------------------------------------------------------

_FALLBACK_HOTKEYS: dict[str, dict[str, str]] = {
    "rgc": {
        "input_menu_toggle_btn": "3",          # SELECT
        "input_exit_emulator_btn": "2",        # START (hold)
        "input_save_state_btn": "11",          # R1
        "input_load_state_btn": "10",          # L1
        "input_fast_forward_btn": "13",        # R2
        "input_rewind_btn": "12",              # L2
        "input_reset_btn": "0",                # A (South)
        "input_volume_up_axis": "+1",
        "input_volume_down_axis": "-1",
        "input_state_slot_increase_btn": "101",
        "input_state_slot_decrease_btn": "100",
    },
    "techdweeb": {
        "input_menu_toggle_btn": "82",         # HOME / MENU
        "input_exit_emulator_btn": "4",        # BACK (hold)
        "input_save_state_btn": "11",          # R1
        "input_load_state_btn": "10",          # L1
        "input_fast_forward_btn": "13",        # R2
        "input_rewind_btn": "12",              # L2
        "input_reset_btn": "0",                # A (South)
        "input_volume_up_axis": "+1",
        "input_volume_down_axis": "-1",
        "input_state_slot_increase_btn": "101",
        "input_state_slot_decrease_btn": "100",
    },
    "merged": {
        # A blend: HOME as menu, SELECT+START to exit (comfortable for most devices)
        "input_menu_toggle_btn": "82",
        "input_exit_emulator_btn": "2",
        "input_save_state_btn": "11",
        "input_load_state_btn": "10",
        "input_fast_forward_btn": "13",
        "input_rewind_btn": "12",
        "input_reset_btn": "0",
        "input_volume_up_axis": "+1",
        "input_volume_down_axis": "-1",
        "input_state_slot_increase_btn": "101",
        "input_state_slot_decrease_btn": "100",
    },
}

# ---------------------------------------------------------------------------
# PPSSPP base INI per device
# ---------------------------------------------------------------------------

_PPSSPP_BASE_INI = textwrap.dedent(
    """\
    [General]
    FirstRun = False
    RunCount = 1
    AutoRun = True
    Browse = False

    [SystemParam]
    PSPModel = 1
    PSPFirmwareVersion = 150

    [Graphics]
    RenderingMode = 1
    SoftwareRendering = False
    HardwareTransform = True
    SWskin = False
    TextureFiltering = 1
    SSAA = False
    FrameSkip = 0
    AutoFrameSkip = True
    FrameRate = 60
    RenderResolution = 2
    AndroidHwScale = 0
    GraphicsBackend = 0
    UseGeometryShader = False
    GpuLogErrorsToConsole = False

    [Sound]
    Enable = True
    AudioBackend = 0
    AudioLatency = 1
    SoundSpeedHack = False

    [Controls]
    HapticFeedback = True
    """
)

# Device-specific PPSSPP overrides
_PPSSPP_DEVICE_OVERRIDES: dict[str, str] = {
    "retroid": "[Graphics]\nRenderResolution = 3\n",
    "odin": "[Graphics]\nRenderResolution = 3\nGraphicsBackend = 1\n",  # Vulkan
    "anbernic": "[Graphics]\nRenderResolution = 2\n",
    "ayaneo": "[Graphics]\nRenderResolution = 3\nGraphicsBackend = 1\n",
    "generic": "",
}

# ---------------------------------------------------------------------------
# Dolphin base INI
# ---------------------------------------------------------------------------

_DOLPHIN_BASE_INI = textwrap.dedent(
    """\
    [Core]
    HLE_BS2 = True
    CPUCore = 1
    Fastmem = True
    FPRF = False
    AccurateNaNs = False
    MMU = False
    DCBZ = False
    SyncGPU = True
    SyncGpuMaxDistance = 100000
    SyncGpuMinDistance = -100000
    SyncGpuOverclock = 1.00000

    [DSP]
    EnableJIT = True
    Backend = OpenSLES

    [Display]
    FullscreenDisplayRes = Auto
    Fullscreen = True
    KeepWindowOnTop = False

    [General]
    ShowActiveTitle = True
    """
)

_DOLPHIN_DEVICE_OVERRIDES: dict[str, str] = {
    "retroid": "[Video_Hardware]\nVSyncSpeed = 0\nBackend = Vulkan\n",
    "odin": "[Video_Hardware]\nBackend = Vulkan\n",
    "anbernic": "[Video_Hardware]\nBackend = OpenGL\n",  # Older SoC
    "ayaneo": "[Video_Hardware]\nBackend = Vulkan\n",
    "generic": "",
}


# ---------------------------------------------------------------------------
# Config generator
# ---------------------------------------------------------------------------


class ControlConfigGenerator:
    """Generate emulator configuration files for popular Android handhelds."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_hotkey_json(standard: str) -> dict[str, str]:
        """Load hotkey bindings from a JSON file, falling back to embedded data."""
        json_path = _HOTKEY_STANDARDS_DIR / f"{standard}.json"
        if json_path.exists():
            try:
                with json_path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "Could not load hotkey JSON for '%s': %s. Using fallback.", standard, exc
                )
        fallback = _FALLBACK_HOTKEYS.get(standard)
        if fallback is None:
            raise ValueError(
                f"Unknown hotkey_standard '{standard}'. "
                f"Valid options: {sorted(_FALLBACK_HOTKEYS.keys())}"
            )
        return fallback

    @staticmethod
    def _get_device_profile(device_type: str) -> dict[str, Any]:
        profile = DEVICE_PROFILES.get(device_type.lower())
        if profile is None:
            logger.warning(
                "Unknown device_type '%s', falling back to 'generic'.", device_type
            )
            profile = DEVICE_PROFILES["generic"]
        return profile

    @staticmethod
    def _dict_to_cfg(mapping: dict[str, str], header: str = "") -> str:
        """Convert a flat dict to a RetroArch .cfg string."""
        lines: list[str] = []
        if header:
            lines.append(f"# {header}")
            lines.append("")
        for key, value in mapping.items():
            lines.append(f"{key} = \"{value}\"")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def generate_retroarch_cfg(
        self, hotkey_standard: str, device_type: str
    ) -> str:
        """Generate a RetroArch hotkey .cfg string.

        Args:
            hotkey_standard: ``'rgc'``, ``'techdweeb'``, or ``'merged'``.
            device_type: ``'retroid'``, ``'odin'``, ``'anbernic'``,
                         ``'ayaneo'``, or ``'generic'``.

        Returns:
            Full RetroArch .cfg file content as a string.
        """
        hotkeys = self._load_hotkey_json(hotkey_standard)
        profile = self._get_device_profile(device_type)

        base_cfg: dict[str, str] = {
            # Video defaults
            "video_fullscreen": "true",
            "video_vsync": "true",
            "video_smooth": "false",
            # Audio defaults
            "audio_enable": "true",
            "audio_latency": "64",
            # Input defaults
            "input_driver": "android",
            "input_joypad_driver": "android",
        }

        # Merge hotkeys
        base_cfg.update(hotkeys)

        # Device-specific button layout
        if profile.get("swap_ab"):
            base_cfg["input_player1_a_btn"] = "1"   # Xbox B position → A
            base_cfg["input_player1_b_btn"] = "0"   # Xbox A position → B
        if profile.get("swap_xy"):
            base_cfg["input_player1_x_btn"] = "3"
            base_cfg["input_player1_y_btn"] = "2"

        # Apply device-specific overrides to raw cfg
        cfg_str = self._dict_to_cfg(
            base_cfg,
            header=(
                f"EmuFlow RetroArch Config | "
                f"Standard: {hotkey_standard} | "
                f"Device: {profile['display_name']}"
            ),
        )
        return self.apply_device_overrides(cfg_str, device_type)

    def generate_ppsspp_ini(self, device_type: str) -> str:
        """Generate a PPSSPP INI configuration string.

        Args:
            device_type: One of the keys in :data:`DEVICE_PROFILES`.

        Returns:
            Full PPSSPP INI file content as a string.
        """
        profile = self._get_device_profile(device_type)
        ini = _PPSSPP_BASE_INI
        override = _PPSSPP_DEVICE_OVERRIDES.get(device_type.lower(), "")

        header = (
            f"# EmuFlow PPSSPP Config | Device: {profile['display_name']}\n"
            f"# Layout: {profile['layout']}\n\n"
        )

        if override:
            # Merge override sections into the base INI
            ini = ini.rstrip("\n") + "\n\n# Device overrides\n" + override

        return header + ini

    def generate_dolphin_ini(self, device_type: str) -> str:
        """Generate a Dolphin INI configuration string.

        Args:
            device_type: One of the keys in :data:`DEVICE_PROFILES`.

        Returns:
            Full Dolphin INI file content as a string.
        """
        profile = self._get_device_profile(device_type)
        ini = _DOLPHIN_BASE_INI
        override = _DOLPHIN_DEVICE_OVERRIDES.get(device_type.lower(), "")

        header = (
            f"# EmuFlow Dolphin Config | Device: {profile['display_name']}\n"
            f"# Layout: {profile['layout']}\n\n"
        )

        if override:
            ini = ini.rstrip("\n") + "\n\n# Device overrides\n" + override

        return header + ini

    def apply_device_overrides(self, config: str, device_type: str) -> str:
        """Apply device-specific patches to any emulator configuration string.

        Current rules:
        - **Retroid**: Ensure Nintendo A/B layout comment is present.
        - **Odin**: Ensure Xbox A/B swap comment is present and note Xbox layout.
        - **Anbernic**: Same as Retroid (Nintendo layout).

        Args:
            config: Existing config string.
            device_type: Device family key.

        Returns:
            Patched configuration string.
        """
        device_type = device_type.lower()
        profile = DEVICE_PROFILES.get(device_type, DEVICE_PROFILES["generic"])

        annotation = (
            f"\n# --- EmuFlow device override: {profile['display_name']} ---\n"
            f"# Button layout: {profile['layout']}\n"
            f"# {profile['description']}\n"
        )

        # Append layout annotation if not already present
        if "EmuFlow device override" not in config:
            config = config.rstrip("\n") + "\n" + annotation

        # Odin / AyaNeo — note the Xbox-style A/B mapping
        if device_type in {"odin", "ayaneo"}:
            if "input_player1_a_btn" not in config:
                config += 'input_player1_a_btn = "1"\n'
                config += 'input_player1_b_btn = "0"\n'
                config += 'input_player1_x_btn = "3"\n'
                config += 'input_player1_y_btn = "2"\n'

        return config
