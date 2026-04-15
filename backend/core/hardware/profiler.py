"""
EmuFlow — Hardware Profiler
Detects chipset identities from Android build info and returns optimal
emulation settings.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("emuflow.profiler")

_CHIPSETS_PATH = Path("/home/user/workspace/emuflow/config/hardware_profiles/chipsets.json")

# ---------------------------------------------------------------------------
# Chipset keyword → normalised chipset_id mapping
# ---------------------------------------------------------------------------

_CHIPSET_KEYWORDS: dict[str, list[str]] = {
    # Qualcomm Snapdragon
    "snapdragon_8_gen3": ["SM8650", "snapdragon 8 gen 3", "8 gen 3"],
    "snapdragon_8_gen2": ["SM8550", "snapdragon 8 gen 2", "8 gen 2"],
    "snapdragon_8_gen1": ["SM8450", "snapdragon 8 gen 1", "8 gen 1"],
    "snapdragon_888":    ["SM8350", "snapdragon 888"],
    "snapdragon_870":    ["SM8250-AC", "snapdragon 870"],
    "snapdragon_865":    ["SM8250", "snapdragon 865"],
    "snapdragon_7s_gen2":["SM7475", "snapdragon 7s gen 2"],
    "snapdragon_7_gen2": ["SM7450", "snapdragon 7 gen 2"],
    "snapdragon_778g":   ["SM7325", "snapdragon 778g"],
    "snapdragon_695":    ["SM6375", "snapdragon 695"],
    "snapdragon_4_gen2": ["SM4450", "snapdragon 4 gen 2"],
    "snapdragon_680":    ["SM6225", "snapdragon 680"],
    # MediaTek Dimensity
    "dimensity_9300":    ["MT6989", "dimensity 9300"],
    "dimensity_9200":    ["MT6985", "dimensity 9200"],
    "dimensity_8300":    ["MT6983", "dimensity 8300"],
    "dimensity_8200":    ["MT6893", "dimensity 8200"],
    "dimensity_1200":    ["MT6893", "dimensity 1200"],
    "dimensity_1100":    ["MT6891", "dimensity 1100"],
    "dimensity_810":     ["MT6833", "dimensity 810"],
    "dimensity_700":     ["MT6833P", "dimensity 700"],
    "helio_g99":         ["MT6789", "helio g99"],
    "helio_g96":         ["MT6781", "helio g96"],
    "helio_g85":         ["MT6769", "helio g85"],
    # Samsung Exynos
    "exynos_2400":       ["S5E9945", "exynos 2400"],
    "exynos_2200":       ["S5E9925", "exynos 2200"],
    "exynos_1380":       ["S5E8835", "exynos 1380"],
    "exynos_1330":       ["S5E8535", "exynos 1330"],
    # Apple (for reference)
    "a17_pro":           ["T8130", "a17 pro"],
    "a16_bionic":        ["T8120", "a16 bionic"],
}


# ---------------------------------------------------------------------------
# Standalone emulator selection matrix
# system → {min_api, package, use_standalone}
# ---------------------------------------------------------------------------

_STANDALONE_MATRIX: dict[str, dict] = {
    "nes":    {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "snes":   {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "gba":    {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "gbc":    {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "gb":     {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "psp":    {"use_standalone": True,  "package": "org.ppsspp.ppsspp", "min_api": 31},
    "ps1":    {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "ps2":    {"use_standalone": True,  "package": "xyz.trixarian.nethersx2", "min_api": 29},
    "gc":     {"use_standalone": True,  "package": "org.dolphinemu.dolphinemu", "min_api": 33},
    "wii":    {"use_standalone": True,  "package": "org.dolphinemu.dolphinemu", "min_api": 33},
    "nds":    {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "3ds":    {"use_standalone": True,  "package": "io.github.lime3ds.android", "min_api": 28},
    "switch": {"use_standalone": True,  "package": "org.sudachi.android", "min_api": 34},
    "genesis":{"use_standalone": False, "package": "com.retroarch", "min_api": 0},
    "n64":    {"use_standalone": False, "package": "com.retroarch", "min_api": 0},
}

# Recommended RetroArch cores per system
_RETROARCH_CORES: dict[str, str] = {
    "nes":     "nestopia_libretro.so",
    "snes":    "snes9x_libretro.so",
    "gba":     "mgba_libretro.so",
    "gbc":     "gambatte_libretro.so",
    "gb":      "gambatte_libretro.so",
    "ps1":     "pcsx_rearmed_libretro.so",
    "nds":     "melonds_libretro.so",
    "genesis": "genesis_plus_gx_libretro.so",
    "n64":     "mupen64plus_next_libretro.so",
    "psp":     "ppsspp_libretro.so",
}

# Chipsets with confirmed Vulkan driver support
_VULKAN_SUPPORTED: set[str] = {
    "snapdragon_8_gen3", "snapdragon_8_gen2", "snapdragon_8_gen1",
    "snapdragon_888", "snapdragon_870", "snapdragon_865",
    "snapdragon_7_gen2", "snapdragon_778g",
    "dimensity_9300", "dimensity_9200", "dimensity_8300", "dimensity_8200",
    "dimensity_1200", "dimensity_1100",
    "exynos_2400", "exynos_2200",
}


class HardwareProfiler:
    """
    Detects Android hardware and derives optimal emulation configurations.
    """

    def detect_chipset_from_build_info(self, build_info: dict) -> str:
        """
        Match a chipset ID from Android build info fields.

        Args:
            build_info: Dict with keys such as 'hardware', 'soc_model',
                        'board', 'manufacturer'. Values are compared
                        case-insensitively against known keywords.

        Returns:
            A normalised chipset_id string (e.g. 'snapdragon_8_gen2') or
            'generic' when no match is found.
        """
        search_text = " ".join(
            str(v).lower() for v in build_info.values() if v
        )

        for chipset_id, keywords in _CHIPSET_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in search_text:
                    logger.info(
                        "Detected chipset '%s' via keyword '%s'",
                        chipset_id, keyword,
                    )
                    return chipset_id

        logger.warning("Could not detect chipset from build_info: %s", build_info)
        return "generic"

    def get_optimal_profile(self, chipset_id: str, system: str) -> dict:
        """
        Return optimal emulation settings for the given chipset and system.

        Loads from chipsets.json when available; otherwise returns sensible
        built-in defaults.

        Args:
            chipset_id: Normalised chipset identifier.
            system:     Target system (e.g. 'psp', 'ps2', 'gba').

        Returns:
            Dict with emulation settings (resolution, renderer, etc.).
        """
        chipsets = self._load_chipsets()
        chip_data = chipsets.get(chipset_id, {})
        systems_data = chip_data.get("systems", {})
        system_profile = systems_data.get(system, {})

        if system_profile:
            return system_profile

        # Built-in defaults
        renderer = self.select_renderer(chipset_id, system)
        return {
            "renderer": renderer,
            "resolution_scale": self._default_resolution_scale(chipset_id),
            "vsync": True,
            "frame_skip": 0,
            "core": _RETROARCH_CORES.get(system),
        }

    def select_renderer(self, chipset_id: str, system: str) -> str:
        """
        Choose between 'vulkan' and 'opengl' for the given chipset and system.

        Rules:
        - PS1 always prefers OpenGL for compatibility (PCSX-ReARMed).
        - NDS prefers OpenGL (melonDS renderer compatibility).
        - All other systems use Vulkan on capable chipsets, OpenGL otherwise.

        Args:
            chipset_id: Normalised chipset identifier.
            system:     Target gaming system.

        Returns:
            'vulkan' or 'opengl'.
        """
        if system in ("ps1", "nds"):
            return "opengl"

        if chipset_id in _VULKAN_SUPPORTED:
            return "vulkan"

        return "opengl"

    def should_use_standalone(
        self, system: str, android_api: int
    ) -> tuple[bool, str]:
        """
        Determine whether a standalone emulator is preferred over a
        RetroArch core for the given system and Android API level.

        Args:
            system:      Target gaming system (e.g. 'psp', 'gc', 'switch').
            android_api: Android API level of the device.

        Returns:
            Tuple of (use_standalone: bool, package_name: str).
            When use_standalone is False, package_name is the RetroArch
            package; when True it is the standalone emulator package.
        """
        entry = _STANDALONE_MATRIX.get(system.lower())
        if entry is None:
            # Unknown system — default to RetroArch
            return False, "com.retroarch"

        if entry["use_standalone"] and android_api >= entry["min_api"]:
            return True, entry["package"]

        # Fall back to RetroArch (core may still apply)
        return False, "com.retroarch"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_chipsets(self) -> dict:
        """Load chipsets.json, returning an empty dict on any error."""
        try:
            with open(_CHIPSETS_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return {}
        except Exception as exc:  # noqa: BLE001
            logger.error("Error loading chipsets.json: %s", exc)
            return {}

    def _default_resolution_scale(self, chipset_id: str) -> int:
        """
        Return a sensible internal resolution multiplier based on chipset tier.

        High-end chips get 3x; mid-range 2x; everything else 1x.
        """
        high_end = {
            "snapdragon_8_gen3", "snapdragon_8_gen2", "snapdragon_8_gen1",
            "dimensity_9300", "dimensity_9200", "exynos_2400", "exynos_2200",
        }
        mid_range = {
            "snapdragon_888", "snapdragon_870", "snapdragon_865",
            "snapdragon_7_gen2", "snapdragon_778g",
            "dimensity_8300", "dimensity_8200", "dimensity_1200",
        }
        if chipset_id in high_end:
            return 3
        if chipset_id in mid_range:
            return 2
        return 1
