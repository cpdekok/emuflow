# 14 — AYANEO Pocket Micro Classic: Device-specifieke Quirks

Status: Draft v1 — operationeel doc voor fase 1 implementatie en troubleshooting.

## Context

De AYANEO Pocket Micro Classic heeft enkele ongebruikelijke hardware- en software-eigenschappen die EmuFlow expliciet moet afhandelen. Dit doc verzamelt ze op één plek.

## Quirk 1: USB-poort met gedeelde data-lines

### Probleem

De USB-C-poort van de Pocket Micro Classic deelt data-lines met de interne controller. Praktisch betekent dit:

- USB-C → USB-C kabel naar PC: ADB werkt vaak alleen als de **interne controller tijdelijk wordt uitgeschakeld** via Android-instellingen of een hardware-toggle
- USB headphones via USB-C werken niet wanneer interne controller actief is
- USB-OTG (externe controller via USB) werkt half — afhankelijk van AYAspace-modus

### EmuFlow-implementatie

**Pre-flight check moet detecteren:**

1. ADB-pairing-attempt faalt → toon AYANEO-specifieke instructie:

> Op de AYANEO Pocket Micro Classic: schakel de interne controller tijdelijk uit via AYAspace > Controller > "Master Universal Controller" toggle. Probeer ADB opnieuw. Na pairing kunt u de controller weer inschakelen — wireless ADB blijft werken.

2. Tijdens onboarding: prioriteer **wireless ADB** boven kabel-ADB. Kabel is alleen voor de eerste pairing-stap nodig.

### Telemetrie

```json
{
  "ayaneo_quirks": {
    "usb_shared_lines_detected": true,
    "wireless_adb_active": true
  }
}
```

## Quirk 2: Geen 3.5mm-jack

### Probleem

Geen analoge audio-jack. Audio gaat via:

- Interne speakers
- Bluetooth (headphones, speakers)
- USB-C (mits interne controller uit, zie Quirk 1)

### EmuFlow-implementatie

Geen directe actie vereist; emulator-audio werkt out-of-the-box via interne speakers. Wel:

- Pre-flight check kan gebruiker informeren ("Voor headphones: gebruik Bluetooth of USB-C-adapter, geen 3.5mm-jack op dit device")
- Overweeg in fase 2: BT-audio-latency-test (BT 5.2 op dit device)

## Quirk 3: Geen analog sticks

### Probleem

Alleen D-pad + ABXY + L1/R1/L2/R2 (tactile). Geen sticks, geen R3/L3.

### EmuFlow-implementatie

**HardwareProfile detecteert** `has_analog_sticks=false` en `controller_layout="no_stick"`.

**Game-library aanpassing:**

- Verberg standaard: N64, GameCube, PS2, Wii (vereisen sticks)
- Markeer met waarschuwing: PS1-games die DualShock-only zijn (Crash Bandicoot 1-3, MGS, Tomb Raider 4+)
- Promoot: GBA, SNES, Genesis, Master System, Game Gear, NES, GB/GBC, PCEngine, NeoGeo Pocket — allen D-pad-native

**Fallback-strategie voor games-met-sticks die toch gespeeld worden:**

- Touchscreen-overlay als virtuele sticks (RetroArch, PPSSPP ondersteunen dit)
- Externe BT-controller (DualSense, Xbox, 8BitDo Pro 2) als gebruiker meer wil

**Default-instellingen per emulator:**

- RetroArch: schakel "analog-to-dpad" mapping uit (kan input verwarren), gebruik native D-pad
- PPSSPP: zet "Show on-screen analog sticks" UIT default, AAN voor games die dat vereisen (vraag bij eerste launch per game)
- DuckStation: kies "DigitalController" als default voor PS1, niet "AnalogController"

## Quirk 4: Tactile (digitale) triggers

### Probleem

L2/R2 zijn tactile switches, geen analoge triggers. Voor de meeste retro-systemen geen probleem (PS1, N64, GameCube hebben analoge triggers). Voor moderne emulatie wel.

### EmuFlow-implementatie

Geen actieve mitigatie nodig in fase 1. Documenteren in `HardwareProfile.has_analog_triggers=false` zodat toekomstige features (racegame-pressure-sensitivity-tips) hiermee rekening houden.

## Quirk 5: AYAspace + Master Universal Controller

### Probleem

AYANEO levert een eigen launcher-suite (AYAspace) en een controller-driver-app (Master Universal Controller). Beide kunnen interferen met:

- Onze knop-mapping (Master Controller doet eigen mapping)
- Onze launcher (AYAspace wil default zijn)

### EmuFlow-implementatie

**Clean-slate wizard voor AYANEO** (default A: vendor-uitschakelen):

```
Te detecteren packages:
- com.ayaneo.ayaspace        (vendor launcher)
- com.ayaneo.master_controller (controller-driver)
- com.ayaneo.gamemanager     (game-bibliotheek)
- com.ayaneo.assistant       (system tray)
```

**Default actie**: alle vier disablen via `pm disable-user --user 0` (Shizuku-vereist).

**Restore-knop blijft beschikbaar**: gebruiker kan AYAspace altijd terugzetten.

**Belangrijk**: Master Universal Controller niet uninstallen, alleen disablen. Bij re-enable krijgt gebruiker zijn vendor-knopmapping terug.

## Quirk 6: 3:2 scherm-aspect (960×640)

### Probleem

Ongebruikelijke aspect-ratio. Voordeel: **perfect voor GBA** (240×160 native is exact 3:2). Nadeel: 16:9-content (PS1-FMVs, modernere ports) krijgt zwarte balken of gestrekt beeld.

### EmuFlow-implementatie

**Per-emulator default-instellingen:**

- RetroArch GBA-core: integer-scaling AAN (4× = 960×640, exact-fit)
- PPSSPP: render-resolutie 1× of 2×, aspect-ratio "auto" met letterbox
- DuckStation: "PAR 4:3" met "Letterbox/Pillarbox" voor PS1

**Library-positionering:** AYANEO Pocket Micro Classic wordt gemarketed als "GBA-perfect handheld". Onze game-aanbevelingen volgen dat.

## Quirk 7: 2600mAh batterij (klein)

### Probleem

Beperkt vergeleken met RP Mini (4000mAh). Battery-leven 4-6 uur bij retro-emulatie, korter bij PSP/PS1.

### EmuFlow-implementatie

- Crash-detectie context-snapshot bevat altijd `battery_level` en `battery_temperature_c`
- Bij <15% battery: rustige notificatie tijdens spel ("Batterij laag, sla op")
- Geen aggressive savestate-trigger op laag battery (UX-besluit: gebruiker beslist zelf)

## Quirk 8: Onbekende AYAspace-permissie-flow

### Probleem (te valideren)

AYAspace kan eigen permission-popups tonen die niet via de standaard Android-flow gaan. Dit kan onze "één-scherm permission-flow" doorbreken.

### EmuFlow-implementatie

**Tijdens fase 1 testen** of dit voorkomt. Indien ja:

- Documenteer welke AYAspace-popups verschijnen
- Voeg ze toe aan onboarding-instructies ("Mogelijk verschijnt een AYAspace-popup, accepteer deze")
- Update `13-hardware-profiles.md` met `permission_flow_quirks` veld

## Samenvatting checklist voor fase 1 testrun

Bij eerste end-to-end test op AYANEO Pocket Micro Classic, verifieer:

- [ ] HardwareProfile detecteert correct: manufacturer=AYANEO, geen sticks, mali-GPU
- [ ] Wireless ADB werkt na initiële kabel-pairing (interne controller-toggle vereist?)
- [ ] Clean-slate wizard detecteert alle 4 AYANEO-packages en disablet ze
- [ ] Restore-knop herstelt AYAspace zonder data-loss
- [ ] RetroArch installeert met OpenGL-ES default (geen Vulkan-poging)
- [ ] GBA-game speelt op 4× integer-scaling perfect zonder zwarte balken
- [ ] FileObserver detecteert saves in `/sdcard/RetroArch/saves/` en kopieert naar Vault
- [ ] Battery-temperatuur in heartbeat klopt
- [ ] Geen ANR's of crashes door gedeelde USB-lines tijdens onboarding

## Open vragen

- Werkt Shizuku zonder modificaties op AYAspace-build van Android 13?
- Heeft AYANEO een eigen "battery-optimization-whitelist" die we moeten omzeilen?
- Is er een hardware-knop om de interne controller uit te zetten zonder Android-instellingen?
- Wordt `Build.SOC_MODEL` correct ingevuld op AYANEO-firmware?
