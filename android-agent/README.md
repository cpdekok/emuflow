# EmuFlow Android Agent

Foundationeel Android-agent skelet voor EmuFlow — de retro-gaming management app voor handheld Android-devices.

**Fase 1 doel-devices:**
- Retroid Pocket Mini (Snapdragon 865, dual sticks)
- AYANEO Pocket Micro Classic (Helio G99, geen sticks)

---

## Overzicht van componenten

### Hardware-detectie

| Bestand | Status | Beschrijving |
|---|---|---|
| `hardware/HardwareProfile.kt` | Volledig | Data class met alle velden (doc 13) |
| `hardware/HardwareProfileDetector.kt` | Volledig | Detecteert SoC, GPU, RAM, controller, display |
| `hardware/DeviceProfileMatcher.kt` | Volledig | Matcht profiel tegen embedded JSON-database |
| `hardware/ControllerDetector.kt` | Volledig | Detecteert sticks, triggers, VID:PID |

### Telemetrie

| Bestand | Status | Beschrijving |
|---|---|---|
| `telemetry/HeartbeatService.kt` | **Stub** | Foreground service, logt payload — geen HTTP |
| `telemetry/HeartbeatPayload.kt` | Volledig | Data class conform backend schema |
| `telemetry/BackendApi.kt` | Volledig | Retrofit interface voor `/devices/heartbeat` |
| `telemetry/DeviceIdManager.kt` | Volledig | UUID genereren en persisteren |

### Crash-rapportage

| Bestand | Status | Beschrijving |
|---|---|---|
| `crash/CrashReporter.kt` | Volledig | Leest `getHistoricalProcessExitReasons` |
| `crash/CrashEvent.kt` | Volledig | Data class voor crash-events |
| `crash/EmulatorPackageRegistry.kt` | Volledig | Register van bekende emulator-packages |

### Save Vault

| Bestand | Status | Beschrijving |
|---|---|---|
| `savevault/SaveWatcherService.kt` | **Stub** | FileObserver aangemaakt, backup-logica stub |
| `savevault/EmulatorSavePathRegistry.kt` | Volledig | Save-paden per emulator (doc 11) |
| `savevault/VaultManager.kt` | Volledig | Kopie + SHA256 + rolling buffer (10 versies) |

### Shizuku-integratie

| Bestand | Status | Beschrijving |
|---|---|---|
| `shizuku/ShizukuManager.kt` | **Stub** | Init, permissie-check, execShell logt maar voert niet uit |

### Permissies

| Bestand | Status | Beschrijving |
|---|---|---|
| `permissions/PermissionBundleManager.kt` | Volledig | Conditionele permissie-check per SDK_INT |

### Clean-slate

| Bestand | Status | Beschrijving |
|---|---|---|
| `cleanslate/VendorShellManager.kt` | **Stub** | Detectie volledig, disable roept ShizukuManager stub aan |

### UI (Compose)

| Bestand | Status | Beschrijving |
|---|---|---|
| `ui/HomeScreen.kt` | Volledig | Status + Resume Last Game knop |
| `ui/PreflightScreen.kt` | Volledig | Één-scherm permission-flow |
| `ui/SettingsScreen.kt` | Volledig | Telemetrie opt-out, vault, clean-slate |
| `ui/theme/EmuFlowAgentTheme.kt` | Volledig | Material 3, dynamic color, dark mode |

---

## Architectuur-diagram

```
┌─────────────────────────────────────────────────────────┐
│                  EmuFlow Android Agent                   │
├─────────────────────────────────────────────────────────┤
│  MainActivity (Compose NavHost)                          │
│    ├── HomeScreen      (status, Resume Last Game)        │
│    ├── PreflightScreen (permission-flow)                 │
│    └── SettingsScreen  (telemetrie opt-out, vault)       │
├─────────────────────────────────────────────────────────┤
│  Foreground Services                                     │
│    ├── HeartbeatService  (60s loop → BackendApi [stub])  │
│    └── SaveWatcherService (FileObserver → VaultManager)  │
├─────────────────────────────────────────────────────────┤
│  Hardware-laag                                           │
│    ├── HardwareProfileDetector  (Build.*, InputDevice)   │
│    └── DeviceProfileMatcher     (assets/profiles.json)   │
├─────────────────────────────────────────────────────────┤
│  System-integratie                                       │
│    ├── ShizukuManager    (pm disable-user, shell [stub]) │
│    ├── CrashReporter     (getHistoricalProcessExitReasons│
│    └── VendorShellManager (clean-slate Retroid/AYANEO)   │
├─────────────────────────────────────────────────────────┤
│  Assets                                                  │
│    └── hardware_profiles.json (RP Mini, AYANEO, fallback)│
└─────────────────────────────────────────────────────────┘

Externe afhankelijkheden:
  ├── Retrofit + OkHttp  → backend-production-05dd.up.railway.app
  ├── Moshi              → JSON parsing
  ├── Shizuku API        → system-level shell (optioneel)
  └── Compose Material 3 → UI
```

---

## Build-instructies

### Vereisten

- **JDK 17** of hoger
- **Android Studio Ladybug** (2024.2.x) of nieuwer
- **Android SDK** met:
  - compileSdk 35 (Android 15)
  - Build Tools 35.x
- Gradle 8.7 (via wrapper)

### Android Studio

1. Open Android Studio
2. `File > Open…` → selecteer `android-agent/`
3. Wacht op Gradle sync
4. Selecteer `app` run-configuratie
5. Klik `▶ Run` (of `Shift+F10`)

### Command-line

```bash
cd android-agent

# Debug APK bouwen
./gradlew assembleDebug

# Release APK bouwen (vereist keystore-configuratie)
./gradlew assembleRelease

# Installeren op verbonden device
./gradlew installDebug

# Unit tests
./gradlew test

# Gradle-taken overzicht
./gradlew tasks
```

### Backend-URL aanpassen

De backend-URL is instelbaar via Gradle-property:

```bash
./gradlew assembleDebug -Pemuflow.backend.url="https://jouw-backend.example.com"
```

Of in `gradle.properties`:
```properties
emuflow.backend.url=https://jouw-backend.example.com
```

---

## Hardware-vereisten voor testen (fase 1)

### Retroid Pocket Mini
- Android 13 (API 33) aanbevolen
- ADB-verbinding via USB-C of wireless ADB
- Shizuku geïnstalleerd en verbonden voor clean-slate test

### AYANEO Pocket Micro Classic
- Android 13 (API 33)
- **Eerste ADB-verbinding**: schakel interne controller tijdelijk uit via AYAspace > Controller > Master Universal Controller toggle
- Wireless ADB opzetten na eerste kabel-koppeling
- Shizuku verbinden voor clean-slate test (AYAspace packages)

---

## Permissie-flow

```
App eerste start
    └── PreflightScreen
            ├── MANAGE_EXTERNAL_STORAGE → Instellingen > Toestaan (alle bestanden)
            ├── POST_NOTIFICATIONS      → Runtime dialog (API 33+)
            └── Shizuku                 → Shizuku app > EmuFlow toegang verlenen
```

---

## Blueprint-documentatie

| Document | Inhoud | Pad |
|---|---|---|
| `11-savestates-vault.md` | Save Vault architectuur, save-paden per emulator | `docs/blueprint/11-savestates-vault.md` |
| `13-hardware-profiles.md` | HardwareProfile schema, profiel-database, detectie | `docs/blueprint/13-hardware-profiles.md` |
| `14-ayaneo-quirks.md` | AYANEO-specifieke quirks (USB, sticks, AYAspace) | `docs/blueprint/14-ayaneo-quirks.md` |

---

## Volgende implementatie-stappen

Zie `team_advice/android_skeleton_status.md` voor de volledige aanbevolen PR-volgorde.

Kort overzicht:
1. **ShizukuManager execShell** — koppelen aan `Shizuku.newProcess()`
2. **HeartbeatService HTTP** — activeer `BackendApi.service.sendHeartbeat()`
3. **SaveWatcherService** — koppelen aan FileObserver + VaultManager
4. **VendorShellManager** — clean-slate wizard end-to-end testen op device
5. **CrashReporter** — koppelen aan heartbeat-telemetrie
6. **UI polish** — Resume Last Game koppelen aan emulator-launch

---

## Privacy-noten

- ROM-hashes worden **nooit** naar de backend verstuurd
- Device-ID is een willekeurige UUID — geen hardware-fingerprinting
- Telemetrie is opt-out via Instellingen > Privacy
- Save Vault data blijft lokaal op het device

Zie `docs/blueprint/11-savestates-vault.md` voor het volledige legal-advies.
