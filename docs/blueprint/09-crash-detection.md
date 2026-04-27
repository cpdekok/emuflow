# 09 — Crashdetectie en Stabiliteits-telemetrie

Status: Draft v1 — fase 1 P0-feature.

## Context

Aanleiding: tester (founder) ervoer regelmatige crashes met God of War op Odin 2 (Snapdragon 8 Gen 2), terwijl die hardware technisch ruim voldoende is. Zonder data is crash-oorzaak onbekend; met data kunnen we per (device, emulator, game-id)-combinatie betrouwbaarheids-scores opbouwen.

Crashdetectie is daarmee niet een fase 4-luxe, maar een fase 1 P0-feature: jouw eigen RP5-test is precies waar we deze data willen verzamelen.

## Doelen

1. Detecteer 95%+ van emulator-crashes (native, ANR, OOM, signaled)
2. Capture context-snapshot zonder game-content te lekken
3. Aggregeer naar (device, emulator, game-id)-stabiliteits-score
4. Waarschuw gebruiker pre-game bij bekend-instabiele combinaties

## Niet-doelen

- ROM-content of game-saves uploaden
- Realtime debugging (developer-tool, niet end-user)
- Auto-fix van crashes (alleen detectie + rapportage)

## Crash-bronnen

Op Android 11+:

- **Native crashes** (SIGSEGV, SIGABRT, SIGILL) — vaak in emulator-libs
- **ANR** (Application Not Responding) — UI-thread-blokkade >5s
- **OOM** (LOW_MEMORY exit) — emulator killed door system_server
- **Forced kill** (SIGKILL) — battery-saver, thermal-protection
- **Java/Kotlin uncaught exceptions** — zeldzaam in emulators (meeste zijn native)
- **Signaled by user** — niet echt een crash, maar wel registreren

## Detectie-mechanismen

### 1. ActivityManager.getHistoricalProcessExitReasons()

API 30+ (perfect voor onze min-SDK 30). Geeft per process-exit:

- `getReason()`: REASON_CRASH, REASON_CRASH_NATIVE, REASON_ANR, REASON_LOW_MEMORY, REASON_SIGNALED, etc.
- `getStatus()`: signal/exit code
- `getDescription()`: korte tekst-beschrijving
- `getTimestamp()`, `getProcessName()`, `getRss()`, `getPss()`
- `getTraceInputStream()`: tombstone of ANR-trace (voor REASON_ANR en REASON_CRASH_NATIVE)

EmuFlow-agent polt dit elke 30s en bij elke heartbeat voor alle bekende emulator-package-names.

### 2. Logcat-tail

Bij detectie van een crash voor een bekende emulator-PID:

- Lees laatste 200 regels logcat van die PID via `Logcat` API
- Filter op stacktraces, fatal-signals, tombstone-paths
- Strip paden die filenames bevatten (regex `/storage/.*\.(iso|bin|cue|chd|nsp|xci)`)

### 3. UncaughtExceptionHandler

Voor de EmuFlow-agent zelf (niet emulators) — vangt eigen crashes en stuurt naar telemetrie.

## Context-snapshot

Bij elke gedetecteerde crash:

```json
{
  "event": "emulator_crash",
  "timestamp": "2026-04-26T20:45:12Z",
  "device_id": "uuid",
  "emulator": {
    "package": "org.ppsspp.ppsspp",
    "version_name": "1.17.1",
    "version_code": 1170100
  },
  "game": {
    "game_id": "ULES01376",
    "platform": "psp",
    "duration_played_sec": 1843
  },
  "crash": {
    "reason": "CRASH_NATIVE",
    "signal": "SIGSEGV",
    "rss_mb": 1842,
    "pss_mb": 1612,
    "stacktrace_hash": "sha256:abc123...",
    "tombstone_excerpt": "..."
  },
  "context": {
    "thermal_state": "MODERATE",
    "battery_level": 0.67,
    "battery_temperature_c": 38.5,
    "free_ram_mb": 412,
    "page_size": 4096,
    "android_release": "13",
    "manufacturer": "AYN",
    "model": "Odin 2"
  }
}
```

## Privacy en juridisch

### Wat we wel sturen

- **Game-ID**: officiële product-code (PSP `ULES01376`, Switch `0100abc...`, GameCube `GAFE01`). Dit is publieke metadata, geen content.
- **Stacktrace-hash**: groepeert identieke crashes zonder PII
- **Tombstone-excerpt**: alleen technische frames, paden gestript

### Wat we NIET sturen

- ROM-bestandsnaam
- ROM-hash (kan content-identificatie geven via NoIntro/Redump-databases)
- Save-state-content
- Memory-dumps

### Opt-in en transparantie

- Eerste-run wizard: expliciete opt-in voor crash-telemetrie, default AAN met duidelijke uitleg
- Settings → "Privacy en telemetrie": altijd opt-out
- Lijst van veldenuits in app raadpleegbaar
- DSA art. 6: blijft schoon, we collecteren geen content

## Aggregatie en dashboard

### Backend-aggregatie

Per (device_model, emulator_package, emulator_version, game_id, android_release):

- `crash_count_24h`, `crash_count_7d`, `crash_count_30d`
- `play_time_total_sec`
- `crashes_per_hour` = `crash_count / (play_time / 3600)`
- `top_stacktrace_hashes` (top 5)

### Intern dashboard (fase 1)

Views:

- **Top instabiele combinaties** (sorted by crashes_per_hour, min 10h speeltijd)
- **Per-emulator stabiliteit** over alle devices
- **Per-device stabiliteit** over alle emulators
- **Trend** over emulator-versies (regression-detectie)
- **Stacktrace-clusters** (top hashes met counts)

### Pre-game waarschuwing (fase 2+)

Wanneer gebruiker een game start:

- Lookup: is deze (device, emulator, game-id) bekend instabiel?
- Drempel: >0.5 crashes/hour over min 100h gemeten speeltijd
- Toon non-blocking toast: "Deze combinatie crasht bij ~23% van spelers. Tip: schakel Vulkan uit."

Tips komen uit gecureerde knowledge-base, niet auto-gegenereerd.

## Backend-schema

Nieuwe tabel `crash_events`:

```sql
CREATE TABLE crash_events (
  id UUID PRIMARY KEY,
  device_id UUID REFERENCES devices(id),
  timestamp TIMESTAMPTZ NOT NULL,
  emulator_package TEXT NOT NULL,
  emulator_version_name TEXT,
  emulator_version_code INTEGER,
  game_id TEXT,
  platform TEXT,
  duration_played_sec INTEGER,
  crash_reason TEXT NOT NULL,
  crash_signal TEXT,
  rss_mb INTEGER,
  pss_mb INTEGER,
  stacktrace_hash TEXT,
  tombstone_excerpt TEXT,
  thermal_state TEXT,
  battery_level REAL,
  battery_temperature_c REAL,
  free_ram_mb INTEGER,
  page_size INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_crash_device ON crash_events(device_id, timestamp DESC);
CREATE INDEX idx_crash_combo ON crash_events(emulator_package, game_id, timestamp DESC);
CREATE INDEX idx_crash_hash ON crash_events(stacktrace_hash);
```

## Endpoint

`POST /devices/crash-events` — agent stuurt batches van crash-events
`GET /admin/crashes/top` — intern, top instabiele combinaties
`GET /admin/crashes/{stacktrace_hash}` — drill-down op stacktrace-cluster

## Roadmap-fases

- **Fase 1**: detectie + context-snapshot + intern dashboard. Eigen RP5-data drijft validatie.
- **Fase 2**: pre-game waarschuwingen, knowledge-base met fix-tips
- **Fase 3**: stacktrace-clustering met embeddings, regression-detection per emulator-update
- **Fase 4**: emulator-developers krijgen geanonimiseerde feed van top-crashes (waarde voor het ecosysteem)

## Acceptance criteria

- Given een emulator crasht (native SIGSEGV)
- When de EmuFlow-agent draait
- Then binnen 60s is een crash_event gepost naar backend met geldige stacktrace_hash en geen ROM-paden in tombstone_excerpt

- Given gebruiker heeft opt-out gegeven
- When emulator crasht
- Then geen crash_event wordt verstuurd, lokaal log-bestand wordt wel bijgehouden voor lokale diagnose

## Open vragen

- Hoe omgaan met emulators die `pm uninstall` werd gedaan tijdens crash-window?
- Tombstone-grootte op disk: limit per device (500KB rolling buffer?)
- Verschil in `getHistoricalProcessExitReasons` betrouwbaarheid tussen vendor-builds onderzoeken
