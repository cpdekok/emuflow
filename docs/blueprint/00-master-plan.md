# EmuFlow Master Plan — van prototype naar self-running business

> Dit document is de blauwdruk voor productlanceringen door Christian de Kok. EmuFlow is de eerste productie; volgende producten volgen ditzelfde proces.

## Visie

EmuFlow geeft elke Android retro-handheld bezitter een Nintendo Switch / Steam Deck-achtige ervaring zonder uren technisch geknoei. Vanaf een lege handheld in 10 minuten naar volledig geconfigureerde emulatie-setup met alle emulatoren, optimale gamepad-mapping en automatische updates.

## Doelgroep (eerste cohort)

Retro-handheld bezitters die:
- Een Android-gebaseerde handheld kochten onder €600 (Retroid Pocket 2/3/4/5/Mini, AYN Odin/Odin 2, Anbernic RG556/RG406V/RG406H, GPD XP/XP Plus, Logitech G Cloud, Razer Edge, etc.)
- Niet de tijd of skills hebben voor handmatig instellen van RetroArch + per-systeem cores + BIOS + controller mappings
- Bereid zijn €5-15/mnd of eenmalig €49-99 te betalen voor "het werkt gewoon"

**Scope-grenzen**:
- ✅ Alle Android-handhelds onder €600 (sub-€600 "value tier" + mid-range)
- ❌ Premium handhelds boven €600 (Steam Deck, ROG Ally, Ayaneo Slide — andere doelgroep, anders ecosysteem)
- ❌ Linux-only handhelds (Anbernic RG35XX, Miyoo Mini, etc.) — andere markt, andere distributie
- ❌ Nintendo Switch / Steam Deck zelf (zijn de inspiratiebron, niet de doelmarkt)

Markt: ~500k-1M actieve gebruikers wereldwijd, groeiend. Subreddits r/SBCGaming (300k+), r/EmulationOnAndroid (200k+).

## 6-fasen plan

### Fase 1 — Solo-test (NU, deze week)
**Doel**: Christian kan op zijn Android-handheld in <10 min van scratch een werkende emulatie-setup krijgen, met agent (mij) die remote alles ziet.

**Deliverables**:
- Android Agent APK (Kotlin + Shizuku) sideloadbaar
- Telemetrie pipeline: handheld → backend → dashboard
- Frontend toont real-time device status (geen `—` placeholders meer)
- Self-test script: `bash scripts/smoketest.sh` doet end-to-end check
- AI cross-validatie review (Claude Code, Codex, Grok, Gemini)

**Exit-criteria**:
- Setup-tijd op kale handheld <10 minuten (gemeten)
- ≥5 emulatoren auto-geïnstalleerd en gemapped (PSP, GBA, NDS, SNES, Genesis minimum)
- Heartbeat zichtbaar in dashboard binnen 30 seconden
- Geen kritieke issues in cross-validatie reports

### Fase 2 — UX afwerking + alle emulatoren
**Doel**: Het voelt als een Switch / Steam Deck. Polish, geen rough edges.

**Deliverables**:
- 12+ emulatoren ondersteund (PS1, PS2, GameCube, Wii, N64, Dreamcast, etc.)
- Onboarding wizard (eerste 5 schermen)
- Game cover art + metadata via screenscraper.fr / IGDB
- Fullscreen "TV mode" voor handhelds
- Foutmeldingen menselijk en oplosbaar

**Exit-criteria**:
- 95% van features werken op 3 verschillende handheld-modellen
- Onboarding-completion >80% in eigen test
- Lighthouse score frontend >90

### Fase 3 — Beta met 2-3 IT-vrienden
**Doel**: Externe validatie van setup, UX en stabiliteit.

**Deliverables**:
- Closed beta access (max 5 testers)
- Feedback-formulier in app (Telegram bot of in-app)
- Bug tracker in GitHub Issues
- Wekelijkse beta-call (15 min)

**Exit-criteria**:
- ≥4 van 5 testers krijgen <30 min werkende setup
- Geen P0 bugs in laatste 7 dagen beta
- NPS ≥7 na 2 weken gebruik

### Fase 4 — Marketing fundament
**Doel**: Klaar voor publieke launch.

**Deliverables**:
- Marketing site (apart van app dashboard) op emuflow.app/landing
- 5 pillar blog posts (SEO: "best emulator setup for Retroid Pocket", etc.)
- YouTube demo-video (3 min)
- Twitter/X account + 30-day content kalender
- Reddit launch-strategie (r/SBCGaming, r/EmulationOnAndroid, r/RetroidPocket)
- Email-capture pre-launch lijst

**Exit-criteria**:
- ≥500 email signups voor launch
- ≥1000 video views in eerste week
- Eerste 3 blog posts op Google Search Console

### Fase 5 — Monetisatie
**Doel**: Eerste betalende klanten.

**Deliverables**:
- Stripe integratie (subscription + one-time)
- Google Play Store listing (internal → closed → open testing → production)
- Pricing pagina met 2 tiers: Free (limited) + Pro (€49 eenmalig of €5/mnd)
- T&C, privacy policy (NL/EN)
- License-key mechanisme

**Exit-criteria**:
- Eerste 10 betalende klanten
- Churn <10% na 30 dagen
- Stripe Atlas / KvK boekhouding op orde

### Fase 6 — Self-running met AI agent
**Doel**: Christian besteedt <2 uur/week aan EmuFlow operations.

**Deliverables**:
- Daily cron job (mij) die rapporteert: nieuwe signups, churn, errors, revenue
- Auto-respons systeem voor support tickets (90% L1 vragen via AI)
- Auto-publicering content (1 blog/week, 3 tweets/week)
- Weekly business review notification op Telegram
- Anomaly-detection alerts (sudden churn, server down, etc.)

**Exit-criteria**:
- €500+ MRR
- <2 uur/week operationeel werk
- Christian kan 2 weken op vakantie zonder iets te doen

## AI cross-validatie cadans

Voor elke fase laat Christian de status reviewen door 4 AI-systemen:
- **Claude Code** — code-review, security, architectuur
- **OpenAI Codex** — code-review, alternatieve implementaties
- **Grok** — businessmodel scherpte, marktpositionering, contrarian view
- **Gemini** — productstrategie, marketingvalidatie

Reviews worden opgeslagen in `docs/blueprint/reviews/<fase>-<ai>.md` en samengevoegd in `docs/blueprint/reviews/<fase>-summary.md`.

## Blauwdruk-aspecten (herbruikbaar)

Onderdelen die we hier bouwen en naar volgende producten kunnen kopiëren:
1. CI/CD pipeline (GitHub → Vercel + Railway)
2. Telemetry/monitoring stack (heartbeat, error reporting, dashboard)
3. AI cross-validatie proces (templates en prompts)
4. Marketing-content pipeline (SEO + social + email)
5. Stripe + Play Store integratie boilerplate
6. Self-running ops dashboard (daily cron met rapportage)
