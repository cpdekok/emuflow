# 08 — Controllers: Detectie, Mapping en Externe Pairing

Status: Draft v1 — fase 1 scope minimaal, fase 2-4 uitgebreid.

## Context

EmuFlow ondersteunt drie device-klassen, elk met eigen controller-realiteit:

- **Handheld** (RP5, Odin 2, RG556): interne controls primair, externe optioneel (docked/tv-out)
- **Tablet**: geen interne controls, externe controller verplicht, clip-on past zelden
- **Phone** (fase 4+): externe verplicht, clip-on werkt wel (Backbone, Kishi)

Een goede controller-flow is een van de drie pijlers waarvoor gebruikers EmuFlow installeren (naast clean-slate en BIOS-flow).

## Doelen

1. Externe controller binnen 60 seconden gepaird en gemapped
2. Bekende controllers (top-20 VID/PID) automatisch correct profiel
3. Hot-swap tussen intern en extern zonder emulator-crash
4. Per-emulator mappings automatisch gegenereerd uit één canoniek profiel

## Niet-doelen

- In-game gameplay-aanpassingen (laten we aan de emulator)
- Custom firmware op controllers
- Concurrentie met Steam Input of vergelijkbaar

## Detectie

### Wat we ophalen

Via Android `InputManager`:

- `getInputDeviceIds()` — alle aangesloten input-devices
- Per device: `getName()`, `getVendorId()`, `getProductId()`, `getSources()`, `getDescriptor()`
- `hasVibrator()`, `hasMicrophone()`, gyroscope/accelerometer via SensorManager
- Connection type: `getInputDevice().isExternal()` — bepaalt intern vs. extern

### Bekende controllers (P0 voor fase 1)

| Merk | VID | Veelvoorkomende producten |
|---|---|---|
| Microsoft Xbox | 045E | Xbox Wireless, Elite |
| Sony | 054C | DualShock 4, DualSense |
| Nintendo | 057E | Switch Pro Controller |
| 8BitDo | 2DC8 | Pro 2, SN30 Pro, Ultimate |
| GameSir | 3537 | X2, X3, T4 Pro |
| Backbone | 358A | One (USB-C, Lightning) |
| Razer | 1532 | Kishi V2 |

Database wordt bijgehouden in `backend/data/controller_profiles.json`, gepusht naar agent via update-channel.

## Profielmodel

Eén canoniek EmuFlow-profiel per controller, daaruit genereren we per emulator:

- RetroArch: `retroarch.cfg` autoconfig-formaat
- Dolphin: `Profiles/GCPad/Profile.ini`
- PPSSPP: `controls.ini`
- DuckStation: `controller.ini`
- AetherSX2: `inis/PAD.ini`

Canoniek profiel-schema (vereenvoudigd):

```json
{
  "controller_id": "8bitdo_pro_2",
  "vid": "0x2DC8",
  "pid": "0x6101",
  "buttons": {
    "south": "BUTTON_A",
    "east": "BUTTON_B",
    "west": "BUTTON_X",
    "north": "BUTTON_Y",
    "l1": "BUTTON_L1",
    "r1": "BUTTON_R1",
    "l2_axis": "AXIS_LTRIGGER",
    "r2_axis": "AXIS_RTRIGGER"
  },
  "axes": {
    "left_stick": ["AXIS_X", "AXIS_Y"],
    "right_stick": ["AXIS_Z", "AXIS_RZ"],
    "dpad": "HAT"
  },
  "features": {
    "rumble": true,
    "gyro": false,
    "battery_via_hid": true
  }
}
```

## Pairing-flow (fase 4 voor tablets/phones)

1. **Scan**: BLE + Classic BT scan, filter op input-device-class
2. **Pair**: Android Companion Device Manager (CDM) flow voor minimale permissies
3. **Verify**: short input-test (druk knop X, beweeg stick)
4. **Match**: VID/PID lookup in database → kies profiel
5. **Push**: schrijf mappings naar elke geïnstalleerde emulator
6. **Save**: persistent profiel per device in EmuFlow-config

## Hot-swap

Probleem: gebruiker speelt met interne controls, switcht naar externe BT-controller mid-game → emulator verliest input of crasht.

Oplossing:

- EmuFlow-agent luistert op `InputManager.InputDeviceListener`
- Bij `onInputDeviceAdded`/`Removed`: bepaal of het de actieve controller is
- Schrijf nieuwe mapping naar emulator-config zonder restart waar mogelijk
- Als emulator restart vereist: graceful prompt aan gebruiker

## Multi-controller (P1)

- 2-4 spelers (Mario Kart, Smash, Bomberman)
- Player-1/2/3/4 toewijzing via UI
- Persistent: laatste-gebruikte player-slot per VID/PID

## Latency-meting (P2)

Optionele tap-test in pre-flight check:

- LED knippert → gebruiker drukt knop → meet tijd tussen visueel signaal en input-event
- Drempels: <15ms uitstekend, 15-25ms speelbaar, >25ms waarschuwing
- Telemetrie-veld: `controller_latency_ms`

## Telemetrie-velden

Toe te voegen aan heartbeat-payload:

```json
{
  "controllers": [
    {
      "vid": "0x2DC8",
      "pid": "0x6101",
      "name_hash": "sha256:...",
      "is_external": true,
      "connection": "bluetooth",
      "profile_matched": true,
      "battery_level": 0.83
    }
  ]
}
```

`name_hash` ipv. naam: privacy + groepering bij rapportage.

## Roadmap-fases

- **Fase 1**: detectie van interne + externe controller, top-20 profielen, single-player
- **Fase 2**: hot-swap, multi-player tot 2 spelers
- **Fase 3**: latency-meting, controller-stats in telemetrie-dashboard
- **Fase 4**: tablet/phone pairing-wizard, multi-player tot 4, clip-on detectie

## Open vragen

- Werkt CDM-flow op alle Android 11+ vendor-builds (Retroid, AYN, Anbernic)?
- Hoe omgaan met Bluetooth-stack-bugs op specifieke chipsets (MediaTek vs. Qualcomm)?
- Vereist DualSense gyro+haptics een aparte permissions-flow?
