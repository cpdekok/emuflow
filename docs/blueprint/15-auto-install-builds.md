# 15 — Auto-install met page-size-aware emulator-builds

> Doc-status: blueprint, fase 1.
> Auteur: COO (Christian de Kok), engineering input via team-overleg 27 apr 2026.
> Scope: matching algoritme dat per device de juiste APK-build kiest.

## 1. Waarom

Android-emulators worden gedistribueerd in steeds meer build-varianten:

- **Page size**: 4 KB (klassiek) versus 16 KB (Android 15 + bepaalde GKI-kernels). Een 16 KB-build crasht direct op een 4 KB-kernel en omgekeerd. Zie de Android 16 KB page support guidance van [Android Developers](https://developer.android.com/guide/practices/page-sizes).
- **ABI**: arm64-v8a is universeel voor onze handhelds; armeabi-v7a is alleen historisch relevant.
- **Renderer**: sommige forks shippen een Vulkan-only en een GL-only build (relevant voor Mali-G57 — doc 14).
- **minSdk**: oudere builds eisen Android 10 of lager; nieuwste versies vereisen Android 12+.

Een gebruiker die handmatig zoekt op GitHub-releases of Google Play kan dit niet betrouwbaar matchen. Een verkeerde build = directe crash bij eerste launch — exact het probleem dat fase 1 oplost (doc 09 crash detection).

## 2. Match-criteria (in volgorde)

EmuFlow Agent kiest per emulator-package één concrete APK aan de hand van:

1. **Page size** moet exact overeenkomen (4 KB ↔ 4 KB, 16 KB ↔ 16 KB).
2. **ABI** = arm64-v8a (alle ondersteunde handhelds zijn 64-bit).
3. **minSdk ≤ device API** en **targetSdk ≥ 30** (anders verbiedt Shizuku silent install).
4. **Renderer voorkeur** uit hardware-profiel (doc 13):
   - Adreno → Vulkan-build wint van OpenGL-ES-build.
   - Mali ouder dan G77 → OpenGL-ES-build wint van Vulkan-build.
5. **Stable > beta > nightly** tenzij gebruiker expliciet "include nightly" heeft aangezet.
6. **Hoogste versie** binnen de gefilterde set.

Als geen enkele build aan 1–3 voldoet → **fail-fast** met heldere boodschap (geen poging tot installatie).

## 3. Bronnen voor builds

EmuFlow gebruikt uitsluitend officiële distributiekanalen — nooit gemirrorde of repackaged builds.

| Emulator    | Bron                                | Type        |
| ----------- | ----------------------------------- | ----------- |
| RetroArch   | GitHub Releases libretro/RetroArch  | Stable+Nightly |
| Citra       | GitHub Releases citra-emu/citra-canary | Canary      |
| Dolphin     | dolphin-emu.org/download            | Stable+Beta+Dev |
| AetherSX2   | aethersx2.com/archive               | Stable      |
| PPSSPP      | ppsspp.org/download                 | Stable+Nightly |
| ePSXe       | Google Play Store (commerciële app) | Stable      |
| DuckStation | GitHub Releases stenzek/duckstation | Stable+Nightly |
| Citra MMJ   | GitHub Releases weihuoya/citra      | Stable      |

Per release halen we metadata op (bestandsnaam, ABI tags in filename, gepubliceerde datum, sha256 van de asset). De match-engine werkt op die metadata, downloadt pas na keuze.

## 4. Fingerprint-extractie uit APK

Wanneer een release-asset niet via filename alle info prijsgeeft, extraheert de Agent post-download (sandbox, voor install):

- `aapt2 dump badging` → minSdk, targetSdk, ABI, native libs.
- ELF-header van een native lib → page size (`PT_LOAD` segment-alignment ≥ 16 KB ⇒ 16 KB-compatible).

De download wordt vervolgens **alleen** geïnstalleerd via Shizuku als die fingerprint matcht. Anders wordt de build verwijderd en gaan we naar de volgende kandidaat.

## 5. Caching

Builds worden gecachet onder `/sdcard/EmuFlow_Cache/<package>/<versie>.apk` met een SHA256-checksum. Bij heractiveren controleert de Agent de checksum voor install. Cache-quotum: 1 GB, LRU-eviction.

## 6. Fallback-strategie

Als de officiële bron rate-limit of 5xx geeft:

1. Wacht max 3× (exponential backoff 5 s, 15 s, 45 s).
2. Daarna: meld in UI dat installatie tijdelijk niet beschikbaar is — geef de directe URL door zodat gebruiker handmatig kan downloaden.
3. Spiegel **nooit** via een third-party APK-mirror (security + auteursrecht risico).

## 7. Telemetrie

De heartbeat krijgt per emulator een veld `installed_emulators[].install_source`:

- `emuflow_auto` (door ons via Shizuku)
- `emuflow_manual` (gebruiker download via fallback URL)
- `vendor_preinstalled` (al aanwezig bij eerste agent-start)
- `unknown_user_install` (gebruiker installeerde zelf buiten EmuFlow om)

Hiermee kan crash-rate per install-source gesegmenteerd worden — cruciaal voor het ontdekken van foute manuele matches tegen de juiste auto-matches.

## 8. Versieblokkades (manual override)

Soms breekt een nieuwe release iets (bijv. Citra Canary 2118 vs 2117). Het backend `/updates/check` endpoint kan een **block** flag retourneren per (package, versionCode), zodat de Agent die versie overslaat tot we de blokkade opheffen.

## 9. Phase 1 scope

Uitgangspunt: **alleen RetroArch + PPSSPP + Citra Canary** voor de twee testdevices (RP Mini, AYANEO Pocket Micro Classic). Andere emulators komen in fase 2.

Voor fase 1 mogen we de match-engine beperken tot:

- Page size match (4 KB voor beide testdevices)
- arm64-v8a only
- Stable-only (nightly opt-in)
- Adreno → Vulkan, Mali → GL-ES (precies onze 2 toestellen)

## 10. Open vragen

| Vraag                                                                | Eigenaar | Blocking |
| -------------------------------------------------------------------- | -------- | -------- |
| Hoe detecteren we 16 KB page-builds als de upstream filename liegt?   | Eng      | nee      |
| Cache-eviction op 1 GB voldoende voor multi-emulator install?         | UX       | nee      |
| Wat als gebruiker WiFi-only update wil afdwingen?                     | PM       | nee      |
| Mogen we BIOS-files uit officiële vendor-archieven bundelen?           | Legal    | **ja**   |

De legal vraag (BIOS) is expliciet **uit scope** voor fase 1: BIOS blijft user-supplied, gevalideerd via SHA-256 hash-check (doc 11 §3 + /legal page §2).
