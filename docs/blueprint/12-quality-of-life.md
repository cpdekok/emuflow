# 12 — Quality of Life Features

Status: Draft v1 — fase 1 minimaal (4 features), fase 2-3 uitgebreid.

## Context

"Just Works" is de kernbelofte van EmuFlow. Quality-of-Life-features (QoL) zijn de feitelijke uitvoering daarvan. Alleen: QoL is breed en risico op scope-creep is reëel. Dit doc legt vast wat we per fase doen en waarom.

Categorisatie volgt vier types:

- **Setup-QoL**: alles voor de eerste-run
- **Tijdens-spel-QoL**: alles tijdens een sessie
- **Onderhoud-QoL**: backups, opruimen, health
- **Library-QoL**: visuele en navigatie-verbeteringen rondom games

## Fase 1 — Setup-QoL bundel (P0)

### 1. Eén-scherm permission-flow

Niet zeven popups achter elkaar. UX-besluit:

- Eén scherm: "EmuFlow heeft drie dingen nodig om goed te werken"
- Drie iconen, drie statuslichten (rood/groen), één knop "Alles instellen"
- Systeem vraagt alle permissies in één sessie

Permissies in scope:
- `MANAGE_EXTERNAL_STORAGE` (Android 11+)
- `POST_NOTIFICATIONS` (Android 13+)
- `FOREGROUND_SERVICE_DATA_SYNC` (Android 14+)
- Battery-optimalisatie uitschakelen
- Shizuku-koppeling

### 2. Storage-check vooraf

- Vrije ruimte controleren voor `/sdcard/EmuFlow_Vault/` (minimaal 2GB aanbevolen)
- Schrijfbaarheid valideren
- Bij microSD aanwezig: vraag of vault op SD of intern moet

### 3. Battery-saver-waarschuwing

Battery-optimalisatie en restrictive-mode kunnen FileObserver-events vertragen of droppen. Bij detectie:

- Rustige notificatie: "EmuFlow heeft batterij-optimalisatie uit nodig om saves veilig te bewaren"
- Eén knop: "Instellingen openen"

### 4. Eenvoudige kabel-detectie

Bij eerste run: detecteer of USB-kabel verbonden is met PC voor ADB-pairing. Toon concrete instructie afhankelijk van staat:

- Geen kabel: "Sluit USB-kabel aan op PC"
- Kabel verbonden, geen ADB: "Schakel ADB-debugging in via Ontwikkelaarsopties"
- ADB actief: "Klaar — koppel via Shizuku"

## Fase 1 — Tijdens-spel-QoL (P0)

### 5. Resume Last Game

Zie `11-savestates-vault.md`. Lichte vorm: launcher onthoudt laatste game, één knop herstart.

### 6. Per-game emulator-binding zichtbaar

Bij launch: korte toast "Start [game] via [emulator] [versie]". Bij crash: telemetrie + nette fallback-melding.

Dit haakt aan op crashdetectie (zie `09-crash-detection.md`).

## Fase 2 (Odin 2 / RG556 / RP5 + tweede device)

### Setup
- Auto-reconnect wireless ADB na reboot
- Permission-bundel uitbreiden met emulator-specifieke permissies (per emulator, on-demand)

### Tijdens-spel
- **Universele rewind** waar emulator dat ondersteunt (RetroArch, PPSSPP): één knop = 10 sec terug
- **Eigen auto-save bij exit** (CTO-risico in fase 1, fase 2 acceptabel met validatie op meer devices)
- Performance-overlay (opt-in): FPS, GPU%, temp, battery

### Onderhoud
- Eén-klik backup: alle saves + states + configs naar `/sdcard/EmuFlow_Backup_{date}.zip`
- Restore-flow na re-flash van vendor-firmware
- Storage-cleanup wizard: oude states detecteren

### Library
- Quick-screenshot als losse utility (lokaal, Legal-geel mits geen sync)

## Fase 3 (5-10 testers)

### Onderhoud
- Health-check rapport: maandelijks, stabiliteit, top-3 emulators, storage-trend
- Cross-device save-sync (zero-knowledge E2EE — Legal-vereiste)

### Library
- Auto-art-fetching uit publieke bronnen (alleen via expliciete user-keuze, geen automatische lookup)
- Game-grouping: serie-detectie
- Recent-played, Favorites, Continue-playing rijen
- Search met fuzzy matching
- Filtering (co-op only, kort-sessie-only)

## Fase 4+

### Familie
- Profielen (meerdere users per device met eigen saves)
- Kindermodus
- Speeltijd-limiet

### Voice & AI
Zie `10-voice-control.md`.

## Wat permanent geschrapt is

- Eigen achievement-systeem ([RetroAchievements](https://retroachievements.org) bestaat al, niet zelf bouwen)
- Cosmetische themes als kernfeature (fase 3 als premium-trigger eventueel)
- Multi-user vóór fase 4 (niet relevant voor solo-tester en early adopters)
- Always-on screen-spectating (privacy + performance)

## UX-principes (overstijgend)

- **Tekst-input vermijden**: handhelds met fysieke controls maken tekst-invoer frustrerend. Geen save-rename, geen slot-labels, geen zoekvelden in fase 1-2.
- **Onzichtbaar werkt beter dan zichtbaar**: backups op achtergrond, geen "Save Vault"-navigatie-bestemming in fase 1.
- **Foutmeldingen zijn rustig**: één duidelijke actie, geen technische teksten, geen popups op willekeurige momenten.
- **Default-aan voor preventieve features, default-uit voor confirmaties**: vault staat aan, pre-overschrijf-bevestiging staat uit (vault dekt het probleem al).

## Acceptance criteria fase 1

- Given eerste run op leeg device
- When gebruiker drukt "Alles instellen"
- Then alle vereiste permissies worden in één sessie aangevraagd, status van elke check zichtbaar

- Given storage onvoldoende (<2GB vrij)
- When permission-flow start
- Then waarschuwing met "Ruimte vrijmaken"-actie verschijnt vóór permissions

- Given laatst-gespeelde game bekend
- When gebruiker opent launcher
- Then "Verder met [game]"-knop is zichtbaar binnen 1 seconde

## Implementatie-architectuur (fase 1)

Setup-QoL is verdeeld over drie modules in de Android Agent:

### `com.emuflow.agent.permissions`
- **PermissionBundleManager** — één-scherm permission-flow. Conditioneel per SDK_INT: POST_NOTIFICATIONS (33+), FOREGROUND_SERVICE_DATA_SYNC (34+), MANAGE_EXTERNAL_STORAGE (30+). Shizuku optioneel.

### `com.emuflow.agent.qol`
- **DeviceHealthChecker** — leest runtime-status uit Android system services (BatteryManager, StatFs, PowerManager). Levert `DeviceHealthSnapshot` met kabel-, batterij-, storage- en thermal-velden.
- **DeviceHealthSnapshot** — datamodel met afgeleide booleans (`warning`, `criticallyLow`, `severe`) zodat UI direct rendert zonder berekeningen.
- **ResumeStateManager** — bewaart laatst-gespeelde combinatie (emulator + ROM-id) in app-private opslag. ROM-id is een lokale SHA256-prefix; nooit naar servers.

### `com.emuflow.agent.hardware`
- **ControllerDetector** + **HardwareProfileDetector** — eenmalig bij setup, plus periodiek voor heartbeat.

### Pipeline bij Setup
1. Pre-flight scherm vraagt `DeviceHealthChecker.snapshot(context)` op.
2. Resultaat per check getoond met groen/oranje/rood-indicatie.
3. Op `criticallyLow`: blokkerende waarschuwing met directe actie-link (vrijmaken, opladen).
4. Permissions afgehandeld via `PermissionBundleManager.requestManageExternalStorage()` enz.
5. Bij voltooiing: clean-slate-keuze (default A: vendor shells DISABLED).
6. **Preserve-set vastleggen** — voordat clean-slate of auto-install draait, scant `ROMScanner` (zie doc 17) alle bekende vendor-paden en markeert aangetroffen ROM-bestanden als preinstalled. Deze set wordt nooit aangeraakt door clean-slate, auto-install of agent-uninstall.

### Pipeline bij Heartbeat
- HeartbeatService roept elke N minuten `DeviceHealthChecker.snapshot()` aan en stuurt thermal_state, battery_level, battery_temperature_c mee in het payload-schema.

### Pipeline bij Resume
- Bij start van een game roept de launcher `ResumeStateManager.saveLastPlayed()` aan.
- Op homepage van EmuFlow leest de UI `readLastPlayed()` en toont "Verder met X" knop.
