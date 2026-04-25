# PRD — Fase 1: Solo-test op Android handheld

## Probleem

Christian heeft een Android handheld en wil testen of EmuFlow het Switch/Steam Deck-gevoel kan leveren. Op dit moment:
- Frontend toont placeholders (`—`) i.p.v. echte data
- Android-agent bestaat niet als werkende APK
- Geen telemetrie pipeline tussen handheld en backend
- Geen manier voor agent (mij) om remote te zien wat er gebeurt
- Setup duurt nog "uren" handmatig

Cost of not solving: zonder werkende solo-test kunnen we niet door naar fase 2 (UX afwerking) en zeker niet naar betatest met IT-vrienden.

## Doelen (gemeten outcomes)

| ID | Goal | Meetwijze | Target |
|---|---|---|---|
| G1 | Setup-tijd op kale handheld | Stopwatch van app-install tot eerste game starten | <10 min |
| G2 | Aantal werkende emulatoren na auto-setup | Telling van geïnstalleerde + functionele emus | ≥5 (PSP, GBA, NDS, SNES, Genesis) |
| G3 | Heartbeat latency handheld → dashboard | Tijd tussen device-event en zichtbaar in dashboard | <30 sec |
| G4 | Frontend toont ECHTE data | 0 placeholder `—` waardes op dashboard bij actief device | 100% |
| G5 | Cross-AI validatie passes | Aantal P0/P1 issues uit reviews | 0 P0, ≤3 P1 |

## Non-goals (expliciet niet in fase 1)

- Geen Play Store listing — sideload APK only
- Geen account-systeem — anonymous device-id is genoeg
- Geen pricing/payments — alles gratis in fase 1
- Geen i18n — alleen Nederlands UI
- Geen game-art scraping (komt fase 2)
- Geen 12+ emulatoren (komt fase 2) — focus op 5
- Geen support voor Linux-only handhelds (Anbernic 600+, RG35XX, etc.)

## User stories

**Story 1 (P0)**: Als Christian wil ik op mijn kale Android handheld de EmuFlow APK installeren via één link, zodat ik niet door instructies hoef.
- Given: Android handheld met internet, USB-debugging niet vereist
- When: ik scan QR-code op emuflow.app/install
- Then: download start automatisch, install dialog verschijnt, geen errors

**Story 2 (P0)**: Als Christian wil ik dat na install de EmuFlow-app me door een 3-stappen onboarding leidt, zodat ik weet wat er gebeurt.
- Given: APK net geïnstalleerd
- When: ik open de app
- Then: zie 3 schermen: (1) welkom, (2) Shizuku activeren, (3) "Setup starten" knop

**Story 3 (P0)**: Als Christian wil ik dat één klik alle benodigde emulatoren installeert, zodat ik niet handmatig naar Play Store hoef.
- Given: Shizuku actief, internet aanwezig
- When: ik klik "Setup starten"
- Then: 5 emulatoren worden gedownload van GitHub Releases / Obtainium en geïnstalleerd, met progress UI

**Story 4 (P0)**: Als Christian wil ik dat mijn handheld zichtbaar is in het web-dashboard binnen 30 seconden, zodat ik weet dat de stack werkt.
- Given: device gekoppeld via setup
- When: ik open https://emuflow.app/devices
- Then: zie mijn device met online-status, hardware info, geïnstalleerde emulatoren

**Story 5 (P1)**: Als Christian wil ik dat de agent (Computer/Perplexity) kan zien wat er op mijn device gebeurt, zodat ik remote support kan krijgen.
- Given: device actief, telemetrie aan
- When: agent opent dashboard
- Then: agent ziet recente events (install/error/launch) van laatste 24u

**Story 6 (P1)**: Als Christian wil ik dat ik fysiek de gamepad voel werken in elke emulator, zodat ik niet per emulator hoef te configureren.
- Given: 5 emulatoren geïnstalleerd
- When: ik open een willekeurige emulator en druk op een knop
- Then: input wordt herkend volgens Retro Game Corps standard mapping

## Technische requirements

### Android Agent (P0)

| Component | Tech | Status nu |
|---|---|---|
| Build systeem | Gradle + Kotlin | Niet geconfigureerd |
| Min SDK | API 26 (Android 8.0) | Te bepalen |
| Target SDK | API 34 (Android 14) | Te bepalen |
| Shizuku integratie | rikka.shizuku:api 13.+ | Niet aanwezig |
| Network library | OkHttp 4.+ + Moshi | Niet aanwezig |
| Heartbeat | WorkManager periodic, 60s interval | Niet aanwezig |
| Device fingerprinting | AndroidID + Build.MODEL hash | Niet aanwezig |
| Emulator install | Via PackageInstaller met Shizuku elevated permissions | Niet aanwezig |
| Gamepad mapping | Schrijf naar emulator-specifieke configs (RetroArch CFG, etc.) | Bestaat als Python-config-generator |

### Backend wijzigingen (P0)

- **Endpoint `POST /devices/heartbeat`** — body: `{device_id, hw_info, installed_apps, battery, storage}` → upsert in Postgres
- **Endpoint `GET /devices/{id}/events`** — recent events feed
- **Endpoint `POST /devices/{id}/events`** — agent uploadt events (install_started, install_done, install_failed, launch, error)
- **Postgres schema**: `devices` tabel + `device_events` tabel (Alembic migratie)
- **CORS**: beperken van `*` naar `https://emuflow.app, https://www.emuflow.app, http://localhost:3000`

### Frontend wijzigingen (P0)

- `app/devices/page.tsx` — toont echte device-lijst i.p.v. placeholders
- `app/devices/[id]/page.tsx` — detail-pagina met events, hardware, emulatoren
- `app/page.tsx` — dashboard stats vullen met echte data via SWR
- `lib/api.ts` — typed API client met auto-retry en error-handling
- WebSocket of SSE voor real-time event-stream (P1 — polling 5s acceptabel voor P0)

### Distributie (P0)

- GitHub Actions workflow: bij tag `v*` → build APK → upload naar GitHub Release
- Pagina `emuflow.app/install` met QR-code + install-instructies
- Versie-check endpoint in backend

## Acceptance criteria (Given/When/Then)

**AC1**: Setup-tijd test
- Given: factory-reset Android handheld (Retroid Pocket of Odin), Wi-Fi geconfigureerd
- When: Christian volgt de install-flow van emuflow.app/install
- Then: stopwatch toont <10 min op moment dat eerste game draait in een emulator

**AC2**: Heartbeat zichtbaar
- Given: device 5 minuten online
- When: agent (mij) opent emuflow.app/devices
- Then: device toont status "online" (groen), laatst gezien <2 min geleden

**AC3**: Frontend echte data
- Given: device met 5 emulatoren geïnstalleerd
- When: dashboard wordt geladen
- Then: stat-kaart "Devices" toont "1", "Emulatoren" toont "5", geen `—`

**AC4**: Cross-AI validatie
- Given: code en docs in `main` branch
- When: 4 AI-systemen (Claude Code, Codex, Grok, Gemini) reviewen
- Then: gecombineerd rapport heeft 0 P0 issues, ≤3 P1 issues

## Open vragen

| ID | Vraag | Owner | Blocking? |
|---|---|---|---|
| Q1 | Welke handheld test Christian eerst? | Christian | Yes — bepaalt eerste smoke-test |
| Q2 | Heeft Christian Android Studio op een werkende machine (Mac Mini offline)? | Christian | Yes — APK build |
| Q3 | Is GitHub Actions enough voor APK build of moet er een lokale build-omgeving zijn? | Agent | No — kunnen GitHub Actions gebruiken |
| Q4 | Welke 5 emulatoren in fase 1? | Agent + Christian | Suggestie: RetroArch (multi-core), AetherSX2 of NetherSX2 (PS2), PPSSPP (PSP), Dolphin (GameCube/Wii), DraStic (NDS) |
| Q5 | Mag agent een GitHub PAT met `repo` scope krijgen voor device → backend telemetry uploaden? | Christian | No — backend handelt af |

## Success metrics na launch fase 1

- Setup-tijd <10 min: ✅ / ❌
- Aantal emulatoren werkend: X van 5
- Heartbeat zichtbaar: ✅ / ❌
- Cross-AI validatie issues: P0=0, P1=X
- Persoonlijke "voelt het als Switch?" score (1-10): X
