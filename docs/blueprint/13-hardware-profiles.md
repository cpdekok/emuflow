# 13 — Hardware-profielen en SoC-strategie

Status: Draft v1 — fase 1 P0, foundationeel voor multi-device-support.

## Context

Retro-handhelds verschillen drastisch in capaciteiten ondanks gelijksoortige Android-versies. Snapdragon vs. MediaTek vs. Allwinner heeft directe gevolgen voor:

- GPU-driverkwaliteit (Vulkan-ready vs. OpenGL-ES-only)
- Realistisch emulatie-plafond (PS2-Switch vs. PSP-ceiling)
- Aanbevolen renderer-instellingen per emulator
- Welke games "speelbaar" of "experimenteel" zijn

Daarnaast varieert de fysieke configuratie: **wel of geen analog sticks**, analoge of digitale triggers, scherm-aspect-ratio. Een one-size-fits-all defaults-set werkt niet.

## Doelen

1. Detecteer hardware-profiel automatisch bij eerste run
2. Pas defaults (renderer, controls, game-aanbevelingen) per profiel aan
3. Database is bijwerkbaar zonder app-update (server-side push)
4. Onbekende devices krijgen veilige fallback-defaults

## Fase 1 doel-devices

| | Retroid Pocket Mini | AYANEO Pocket Micro Classic |
|---|---|---|
| **SoC** | Snapdragon 865 | MediaTek Helio G99 |
| **GPU** | Adreno 650 | Mali-G57 MC2 |
| **RAM** | 6GB LPDDR4X | 6/8GB LPDDR4X |
| **Scherm** | 3.7" AMOLED 1280×960 (4:3) | 3.5" IPS 960×640 (3:2) |
| **OS** | Android 13 (v2) of 10→13 | Android 13 |
| **Sticks** | Hall-effect, dubbel | **Geen sticks** |
| **Triggers** | Analoog L2/R2 | Tactile-switch (digitaal) |
| **Vendor-shell** | Retroid Launcher | AYAspace + Master Universal Controller |
| **USB-poort** | USB-C, normale OTG | USB-C 2.0 OTG, **gedeelde data-lines met interne controller** |
| **Audio jack** | 3.5mm aanwezig | Geen, alleen BT of USB-C |
| **Realistisch plafond** | PSP/N64/PS1 vlot, GameCube/PS2 randje | PS1/PSP licht, GBA/SNES sweet spot |

## Detectie

### Wat de agent ophaalt

Bij eerste run en bij elke heartbeat:

```kotlin
data class HardwareProfile(
  val manufacturer: String,        // Build.MANUFACTURER
  val model: String,                // Build.MODEL
  val androidRelease: String,       // Build.VERSION.RELEASE
  val androidApi: Int,              // Build.VERSION.SDK_INT
  val socVendor: String,            // afgeleid uit Build.HARDWARE / Build.SOC_MANUFACTURER (API 31+)
  val socChip: String,              // Build.SOC_MODEL (API 31+) of fallback parsing
  val gpuFamily: String,            // detect via OpenGL-ES context: "adreno" / "mali" / "powervr"
  val pageSize: Int,                // sysconf(_SC_PAGESIZE)
  val ramMb: Int,                   // ActivityManager.MemoryInfo.totalMem
  val displayWidth: Int,
  val displayHeight: Int,
  val displayDensity: Int,
  val hasAnalogSticks: Boolean,     // InputDevice axis-detection
  val hasAnalogTriggers: Boolean,
  val controllerLayout: String,     // "dual_stick", "no_stick", "single_stick"
  val internalGamepadVidPid: String?,
  val vendorShellPackages: List<String>,
  val isShizukuAvailable: Boolean,
  val shizukuVersion: Int?,
  val isRooted: Boolean
)
```

### Sticks-detectie

```kotlin
val internalGamepad = InputDevice.getDeviceIds()
  .map { InputDevice.getDevice(it) }
  .firstOrNull { it.sources and InputDevice.SOURCE_GAMEPAD != 0 && !it.isExternal }

val hasAnalogSticks = internalGamepad?.let { device ->
  device.getMotionRange(MotionEvent.AXIS_X) != null
    && device.getMotionRange(MotionEvent.AXIS_Y) != null
} ?: false
```

### SoC-vendor-detectie

Op API 31+ direct via `Build.SOC_MANUFACTURER` en `Build.SOC_MODEL`. Op lager: parse `Build.HARDWARE` met heuristiek:

- "qcom" / "sdm" / "sm" → Qualcomm Snapdragon
- "mt" → MediaTek
- "exynos" → Samsung Exynos
- "kirin" → HiSilicon
- "rk" → Rockchip
- "sun" → Allwinner

### Vendor-shell-detectie

Lijst van bekende vendor-packages bij elke heartbeat scannen via `PackageManager`:

- `com.retroid.launcher`, `com.retroid.*`
- `com.ayaneo.ayaspace`, `com.ayaneo.master_controller`, `com.ayaneo.*`
- `com.ayn.console`, `com.ayn.*`
- `com.anbernic.*`
- `com.gpd.*`

## Profielen-database

### Schema

```json
{
  "version": "1.0",
  "updated_at": "2026-04-27T11:00:00Z",
  "profiles": [
    {
      "match": {
        "manufacturer": "Retroid",
        "model": "Pocket Mini"
      },
      "device_class": "handheld",
      "soc_vendor": "qualcomm",
      "soc_chip": "Snapdragon 865",
      "gpu_family": "adreno",
      "default_renderer": "vulkan",
      "vulkan_recommended": true,
      "max_realistic_platform": "ps2_light",
      "supported_platforms": [
        "gb", "gbc", "gba", "nes", "snes", "genesis", "n64",
        "ps1", "psp", "ds", "dreamcast", "saturn"
      ],
      "experimental_platforms": [
        "gamecube", "wii", "ps2", "switch_homebrew"
      ],
      "has_analog_sticks": true,
      "controller_layout": "dual_stick",
      "vendor_packages": ["com.retroid.launcher", "com.retroid.console"],
      "page_size_default": 4096,
      "notes": [
        "Snapdragon 865 + Adreno 650: Vulkan-driver kwaliteit goed",
        "AetherSX2 PS2 redelijk speelbaar met optimalisaties",
        "Dolphin GameCube goed, Wii randje"
      ]
    },
    {
      "match": {
        "manufacturer": "AYANEO",
        "model": "AYANEO Pocket Micro Classic"
      },
      "device_class": "handheld",
      "soc_vendor": "mediatek",
      "soc_chip": "Helio G99",
      "gpu_family": "mali",
      "default_renderer": "opengl_es",
      "vulkan_recommended": false,
      "max_realistic_platform": "psp",
      "supported_platforms": [
        "gb", "gbc", "gba", "gg", "sms", "nes", "snes",
        "genesis", "pce", "neogeo_pocket", "ps1_light", "psp_light"
      ],
      "experimental_platforms": ["n64", "ds"],
      "has_analog_sticks": false,
      "controller_layout": "no_stick",
      "vendor_packages": [
        "com.ayaneo.ayaspace",
        "com.ayaneo.master_controller",
        "com.ayaneo.gamemanager"
      ],
      "page_size_default": 4096,
      "quirks": [
        "usb_shared_data_lines",
        "no_headphone_jack",
        "tactile_triggers_only"
      ],
      "notes": [
        "MediaTek Helio G99 + Mali-G57: Vulkan-drivers berucht slecht, OpenGL-ES default",
        "Sweet spot is GBA/SNES/GG (3:2 scherm-aspect ideaal voor GBA)",
        "PS1 en PSP werken licht, geen GameCube/PS2/Wii ambities",
        "USB-poort heeft gedeelde data-lines met interne controller — bij ADB-issues kan tijdelijk uitschakelen interne controller helpen"
      ]
    }
  ],
  "fallback": {
    "device_class": "unknown",
    "soc_vendor": "unknown",
    "default_renderer": "opengl_es",
    "vulkan_recommended": false,
    "max_realistic_platform": "psp",
    "supported_platforms": ["gb", "gbc", "gba", "nes", "snes", "genesis", "ps1"],
    "experimental_platforms": ["psp", "n64"],
    "has_analog_sticks": null,
    "notes": ["Onbekend device — gebruikt veilige defaults"]
  }
}
```

### Distributie

- Geboard in APK met versie 1.0
- Backend-endpoint `/profiles/hardware` levert nieuwere versie bij heartbeat
- Agent caches lokaal, refresht maximaal eens per dag

### Matching-prioriteit

1. Exact match op `manufacturer + model`
2. Match op `soc_chip` (bijv. alle Helio G99-devices)
3. Match op `soc_vendor + gpu_family`
4. Fallback-defaults

## Renderer-strategie

Per (emulator, gpu_family) combinatie hebben we een aanbevolen renderer:

| Emulator | Adreno (Snapdragon) | Mali (MediaTek) | PowerVR (oude) |
|---|---|---|---|
| RetroArch | Vulkan | OpenGL-ES | OpenGL-ES |
| PPSSPP | Vulkan | OpenGL-ES | OpenGL-ES |
| Dolphin | Vulkan | OpenGL-ES | n.v.t. |
| DuckStation | Vulkan | Vulkan (test) of OpenGL-ES | OpenGL-ES |
| AetherSX2 | Vulkan | n.v.t. (te zwaar) | n.v.t. |

EmuFlow zet defaults bij installatie, gebruiker kan altijd handmatig wijzigen.

## Game-aanbevelingen

Per `supported_platforms` toont EmuFlow alleen "groen-vlag"-games. `experimental_platforms` worden gemarkeerd met een waarschuwing ("kan instabiel zijn op dit device").

Voor AYANEO Pocket Micro Classic specifiek:

- Geen N64, GameCube, PS2, Wii in standaard library-suggesties
- GBA-titels prominent (Pokémon, Mario Advance, Zelda Minish Cap)
- SNES en Genesis gepromoot vanwege ideale 3:2 scherm

## Telemetrie-velden

Toevoegen aan heartbeat:

```json
{
  "hardware": {
    "manufacturer": "AYANEO",
    "model": "AYANEO Pocket Micro Classic",
    "android_release": "13",
    "android_api": 33,
    "soc_vendor": "mediatek",
    "soc_chip": "Helio G99",
    "gpu_family": "mali",
    "page_size": 4096,
    "ram_mb": 6144,
    "has_analog_sticks": false,
    "controller_layout": "no_stick",
    "shizuku_available": true,
    "shizuku_version": 13,
    "is_rooted": false
  }
}
```

## Acceptance criteria

- Given een Retroid Pocket Mini bij eerste run
- When agent start
- Then HardwareProfile detecteert manufacturer="Retroid", model="Pocket Mini", soc_vendor="qualcomm", has_analog_sticks=true en kiest profile id "retroid_pocket_mini"

- Given een AYANEO Pocket Micro Classic bij eerste run
- When agent start
- Then HardwareProfile detecteert manufacturer="AYANEO", soc_vendor="mediatek", has_analog_sticks=false en kiest renderer "opengl_es" als default

- Given een onbekend device (bijv. Anbernic RG-toekomst)
- When agent start
- Then fallback-defaults worden toegepast en device wordt geregistreerd als "unknown" voor manuele review

## Open vragen

- Hoe matchen we devices die ROCKNIX of GammaOS draaien (ander Build.MODEL)?
- Hoe omgaan met userspace-modificaties die `Build.MANUFACTURER` aanpassen?
- Moet `ramMb` invloed hebben op `max_realistic_platform`? (8GB AYANEO ≠ 6GB-versie)
