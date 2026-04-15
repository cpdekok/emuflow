# EmuFlow

**Automated emulator deployment, configuration & management for Android retro handhelds.**

EmuFlow detecteert je hardware, selecteert optimale emulatie-instellingen, deployt controller configs via Shizuku/ADB, en houdt al je emulatoren automatisch up-to-date — zonder root.

---

## Inhoudsopgave

- [Wat doet EmuFlow?](#wat-doet-emuflow)
- [Architectuur](#architectuur)
- [Repository structuur](#repository-structuur)
- [Controller Standards](#controller-standards)
  - [Retro Game Corps Standard](#retro-game-corps-standard)
  - [TechDweeb Standard](#techdweeb-standard)
- [Hardware Profiling](#hardware-profiling)
- [Emulator Selectie-Matrix](#emulator-selectie-matrix)
- [Automatische Updates (Obtainium)](#automatische-updates-obtainium)
- [AI Customer Support](#ai-customer-support)
- [BIOS Integrity Check](#bios-integrity-check)
- [Installatie & Development](#installatie--development)
- [Roadmap](#roadmap)
- [Bijdragen](#bijdragen)

---

## Wat doet EmuFlow?

| Functie | Beschrijving |
|---------|-------------|
| **Hardware Profiling** | Detecteert chipset (T618, Dimensity, Snapdragon, etc.) en laadt optimale instellingen |
| **Scoped Storage Deploy** | Schrijft `.cfg`/`.ini` direct naar `/Android/data/` via Shizuku of Wireless ADB |
| **Controller Config** | Past RGC- of TechDweeb-hotkey standaard toe op alle emulatoren in één klik |
| **Emulator Selectie** | Kiest automatisch RetroArch core vs. standalone op basis van Android API-versie |
| **Update Checker** | Periodieke GitHub release checks voor alle emulatoren via Obtainium-protocol |
| **BIOS Verificatie** | MD5-hash check vóór koppeling aan emulatoren — nooit ongeldig BIOS linken |
| **AI Support** | Ingebouwde support-agent op basis van RGC en TechDweeb kennisbank |

---

## Architectuur

```
┌─────────────────────────────────────────────────────────┐
│  EmuFlow Cloud Backend (FastAPI + PostgreSQL + Redis)   │
│                                                         │
│  /devices   /profiles   /bios   /controls               │
│  /updates   /support                                    │
├─────────────────────────────────────────────────────────┤
│  EmuFlow Android Agent (Kotlin APK)                     │
│                                                         │
│  DeviceProfiler  →  ScopedStorageDeployer               │
│  ObtainiumBridge →  HotKeyApplier                       │
├─────────────────────────────────────────────────────────┤
│  Device Layer                                           │
│                                                         │
│  /Android/data/   ES-DE   Daijishō   Obtainium          │
└─────────────────────────────────────────────────────────┘
```

**Tech Stack**

| Laag | Technologie |
|------|------------|
| Backend API | FastAPI + Uvicorn |
| Database | PostgreSQL + Redis |
| Auth | Supabase Auth / JWT |
| File Storage | Supabase Storage / Cloudflare R2 |
| Android Agent | Kotlin + Shizuku API |
| Update Tracking | Obtainium-protocol (GitHub Releases API) |
| AI Support | OpenAI GPT-4o-mini of Ollama (lokaal) |
| Frontend | Next.js 14 + Tailwind CSS |
| Hosting | Railway / Fly.io |
| CI/CD | GitHub Actions |

---

## Repository Structuur

```
emuflow/
│
├── .github/
│   └── workflows/
│       └── ci.yml                    # Tests, config validatie, emulator update checks
│
├── android-agent/                    # Kotlin Android APK
│   └── src/main/kotlin/com/emuflow/
│       ├── deployer/
│       │   └── ScopedStorageDeployer.kt   # Shizuku/ADB config deployment
│       ├── profiler/
│       │   └── DeviceProfiler.kt          # Hardware detectie (chipset, RAM, Vulkan)
│       └── updater/
│           └── ObtainiumBridge.kt         # GitHub update checks + Obtainium integratie
│
├── backend/                          # Python FastAPI backend
│   ├── main.py                       # App entry point, routers, CORS
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── api/
│   │   └── routers/
│   │       ├── devices.py            # Device registratie & profiel ophalen
│   │       ├── profiles.py           # Chipset hardware profielen
│   │       ├── bios.py               # BIOS hash validatie
│   │       ├── controls.py           # Controller profiel deployment
│   │       ├── updates.py            # Emulator update management
│   │       └── support.py            # AI support chat
│   ├── core/
│   │   ├── hardware/
│   │   │   └── profiler.py           # Chipset detectie & renderer selectie
│   │   ├── bios/
│   │   │   └── checker.py            # MD5 BIOS integrity checker
│   │   ├── controls/
│   │   │   └── config_generator.py   # Genereert cfg/ini per emulator & device
│   │   └── updater/
│   │       ├── obtainium_service.py  # Async GitHub release checker
│   │       └── scheduler.py         # APScheduler periodieke update jobs
│   ├── db/
│   │   └── migrations/               # Alembic migraties
│   └── services/
│       └── ai_support/
│           ├── support_agent.py      # AI support agent (OpenAI/Ollama)
│           └── knowledge_base.py     # RGC + TechDweeb kennisbank
│
├── config/                           # Alle configuratie-templates
│   ├── hardware_profiles/
│   │   └── chipsets.json             # 6 chipsets × 7 systemen = 42 profielen
│   ├── hotkey_standards/
│   │   ├── rgc_standard.json         # Retro Game Corps standaard
│   │   ├── techdweeb_standard.json   # TechDweeb standaard
│   │   └── merged_default.json       # EmuFlow default (beste van beide)
│   └── controller_profiles/
│       ├── retroarch/
│       │   ├── retroarch_base.cfg    # Basis RetroArch instellingen
│       │   ├── retroarch_rgc.cfg     # RGC hotkey bindings
│       │   └── retroarch_techdweeb.cfg  # TechDweeb hotkey bindings
│       ├── ppsspp/
│       │   └── ppsspp_controls.ini
│       ├── dolphin/
│       │   └── GCPadNew.ini
│       ├── drastic/
│       │   └── drastic_controls.json
│       ├── nethersx2/
│       │   └── PCSX2.ini
│       └── lime3ds/
│           └── qt-config.ini
│
├── frontend/                         # Next.js dashboard
│   ├── components/
│   ├── pages/
│   └── styles/
│
├── scripts/
│   ├── check_emulator_updates.py     # CLI update checker (ook als GitHub Action)
│   └── validate_configs.py           # JSON/INI config validatie voor CI
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docs/
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## Controller Standards

EmuFlow ondersteunt twee community-standaarden en een gecombineerde default.

### Retro Game Corps Standard

Gebaseerd op de [RetroArch Starter Guide](https://retrogamecorps.com/2022/02/28/retroarch-starter-guide/) van Russ (Retro Game Corps).

| Combo | Actie |
|-------|-------|
| `SELECT` | Hotkey Enable (modifier — houd ingedrukt) |
| `SELECT + START` | Quit / Close Content |
| `SELECT + R1` | Save State |
| `SELECT + L1` | Load State |
| `SELECT + R2` | Fast Forward (Toggle) |
| `SELECT + L2` | Rewind (vereist Rewind: AAN per core) |
| `SELECT + X` | Menu Toggle (Quick Menu) |
| `SELECT + Y` | FPS weergave aan/uit |
| `SELECT + B` | Reset Game |
| `SELECT + D-pad ↑` | Run-Ahead aan/uit (latency reductie) |
| `SELECT + D-pad ↓` | Volume omlaag |
| `Hold START (2s)` | Menu Toggle (alternatief) |

**Aanbevolen instellingen:**
- `Auto Save State`: AAN
- `Auto Load State`: AAN
- `Confirm Quit`: UIT (één druk volstaat)
- `Overlay verbergen bij controller`: AAN
- `Rewind`: UIT globaal, AAN per core voor SNES en lager
- `Run-Ahead`: AAN als core override voor systemen met hoge latency op Bluetooth

> ⚠️ Wijs nooit hotkeys toe aan `A` of `B` in de Android versie van RetroArch — dit veroorzaakt een bekende bug waarbij RetroArch opnieuw geïnstalleerd moet worden.

---

### TechDweeb Standard

Gebaseerd op de guides [Set Up Your Android Handheld The BEST Way!](https://www.youtube.com/watch?v=OrNFaSGl3KU) en [Start-to-Finish COMPLETE Android Emulation Setup](https://www.youtube.com/watch?v=tETxR8nFTDE) van TechDweeb.

| Combo | Actie |
|-------|-------|
| `SELECT` | Hotkey Enable (of apparaat-specifieke hotkey knop) |
| `SELECT + A` | Menu Toggle (Quick Menu) |
| `L3 + R3` | Menu Toggle (backup combo) |
| `SELECT + START` | Quit |
| `SELECT + R1` | Save State |
| `SELECT + L1` | Load State |
| `SELECT + D-pad →` | Volgende Save Slot |
| `SELECT + D-pad ←` | Vorige Save Slot |
| `SELECT + R2` | Fast Forward |
| `SELECT + L2` | Slow Motion |
| `SELECT + D-pad ↑` | Volume omhoog |
| `SELECT + D-pad ↓` | Volume omlaag |
| `SELECT + Y` | Screenshot |

**Aanvullende TechDweeb instellingen:**
- `input_block_timeout = 1` — verplicht op Android om dubbele inputs te voorkomen
- `Analog to Digital`: Left Analog (voor systemen zonder analoge stick)
- `Confirm Quit`: UIT
- `Menu Driver`: Ozone (voor Android handhelds, vervangt het standaard GLUI menu)
- `Menu Swap OK/Cancel`: UIT (zodat A bevestigt en B annuleert, Nintendo-layout)

**Per emulator extra:**

| Emulator | TechDweeb aanbeveling |
|----------|-----------------------|
| DraStic (NDS) | L2 = Screen Swap, R2 = Menu, R3 = Pointer Down, Right Stick = Pointer Mode |
| Dolphin (GC/Wii) | Gebruik automatische controller mapping, daarna handmatig corrigeren |
| PPSSPP | Standalone boven RetroArch core vanaf Android API 31 |
| ES-DE | Instellen als standaard Android launcher (Home App) |

---

## Hardware Profiling

EmuFlow detecteert je chipset automatisch via Android `Build.HARDWARE`, `Build.SOC_MODEL` en `/proc/cpuinfo` en laadt het bijbehorende profiel uit `chipsets.json`.

**Ondersteunde chipsets (MVP):**

| Chipset | Vulkan | GPU | Typisch RAM |
|---------|--------|-----|------------|
| Unisoc T618 | Nee | Mali-G52 | 4 GB |
| Helio G99 | Ja | Mali-G57 | 8 GB |
| Dimensity 1100 | Ja | Mali-G77 | 8 GB |
| Snapdragon 865 | Ja | Adreno 650 | 8 GB |
| Snapdragon 8 Gen 1 | Ja | Adreno 730 | 12 GB |
| Snapdragon 8 Gen 2 | Ja | Adreno 740 | 12 GB |

---

## Emulator Selectie-Matrix

| Systeem | API < 30 | API 30–32 | API 33+ |
|---------|----------|-----------|---------|
| NES / SNES / GBA | Nestopia / Snes9x / mGBA core | ← | ← |
| NDS | melonDS core | melonDS core | **DraStic** standalone |
| PSP | PPSSPP core | **PPSSPP standalone** | **PPSSPP standalone** |
| PS1 | PCSX-ReARMed core | ← | ← |
| PS2 | — | **NetherSX2** | **NetherSX2** |
| GameCube / Wii | Dolphin core | Dolphin core | **Dolphin standalone** |
| 3DS | Citra core | **Lime3DS** | **Lime3DS** |
| Switch | — | — | **Sudachi** (SD 8 Gen 1+) |

---

## Automatische Updates (Obtainium)

EmuFlow gebruikt het Obtainium-protocol om emulator updates bij te houden via GitHub Releases.

**Hoe het werkt:**
1. De backend checkt periodiek (standaard elke 24 uur) de GitHub releases van alle emulatoren
2. Bij een nieuwe versie: notificatie via de EmuFlow app + optionele GitHub Issue aanmaken
3. Op het device: EmuFlow kan Obtainium aansturen via `ObtainiumBridge.kt` om direct te updaten

**Gevolgde emulatoren:**
- RetroArch (`libretro/RetroArch`)
- Dolphin Emulator (`dolphin-emu/dolphin`)
- PPSSPP (`hrydgard/ppsspp`)
- NetherSX2 (`Trixarian/NetherSX2-patch`)
- Lime3DS (`Lime3DS/Lime3DS`)
- ES-DE (`ES-DE/emulationstation-de`)
- Obtainium zelf (`ImranR98/Obtainium`)
- Sudachi (`sudachi-emu/sudachi`)

**Handmatige check uitvoeren:**
```bash
python scripts/check_emulator_updates.py
```

---

## AI Customer Support

EmuFlow heeft een ingebouwde support-agent gebaseerd op de kennisbanken van Retro Game Corps en TechDweeb.

**Endpoint:**
```
POST /support/chat
{
  "message": "Mijn PPSSPP heeft last van input lag",
  "conversation_history": [],
  "device_context": {
    "chipset": "dimensity_1100",
    "android_api": 33
  }
}
```

**De agent helpt met:**
- Installatie en configuratie van alle emulatoren
- Controller setup en hotkey problemen
- BIOS ontbreekt of klopt niet
- Hardware compatibiliteit vragen
- ES-DE en Daijishō frontend setup
- Obtainium update problemen

**Provider instelling** (in `.env`):
```env
SUPPORT_AI_PROVIDER=openai        # of: ollama (gratis, lokaal)
OPENAI_MODEL=gpt-4o-mini
```

---

## BIOS Integrity Check

EmuFlow verifieert BIOS-bestanden via MD5-hashes **vóór** koppeling aan een emulator.

```
POST /bios/validate
[
  {"filename": "scph1001.bin", "md5": "924e392ed05558ffdb115408c263dccf"},
  {"filename": "dc_boot.bin",  "md5": "e10c53c2f8b90bab96ead2d368858623"}
]
```

Resultaat per bestand: `passed` / `failed` / `unknown`

> **Belangrijk:** EmuFlow distribueert nooit BIOS-bestanden. Alleen de hash-validatielogica is ingebouwd.

---

## Installatie & Development

### Vereisten
- Python 3.12+
- Docker & Docker Compose
- Android device met Shizuku (aanbevolen) of Wireless ADB

### Snel starten

```bash
# 1. Repository clonen
git clone https://github.com/jouwgebruikersnaam/emuflow.git
cd emuflow

# 2. Environment instellen
cp .env.example .env
# Vul OPENAI_API_KEY, GITHUB_TOKEN etc. in

# 3. Starten met Docker Compose
docker compose up -d

# 4. API beschikbaar op
# http://localhost:8000
# http://localhost:8000/docs  (Swagger UI)

# 5. Frontend
cd frontend && npm install && npm run dev
# http://localhost:3000
```

### Backend alleen (zonder Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Tests uitvoeren

```bash
cd backend
pytest tests/ -v
```

### Config validatie

```bash
python scripts/validate_configs.py
```

---

## Roadmap

### MVP (v0.1) — Fase 1–4 (16 weken)
- [x] Hardware profiling (6 chipsets)
- [x] Scoped Storage deployer (Shizuku + ADB)
- [x] Controller config templates (RGC + TechDweeb)
- [x] BIOS integrity checker
- [x] Emulator selectie-matrix
- [x] Obtainium update service
- [x] AI support agent
- [ ] Android Agent APK build & release
- [ ] Next.js dashboard (device beheer, one-tap deploy)
- [ ] Supabase productie-database
- [ ] OTA config updates via Supabase Realtime

### v0.2 — Community Features
- [ ] Community chipset PRs (GitHub-model zoals libretro/libretro-database)
- [ ] Skin/theme repository integratie
- [ ] Daijishō platform-export automatisering
- [ ] ES-DE symlink generator
- [ ] Multi-device beheer

### v1.0 — Stabiele Release
- [ ] Alle chipsets in de top-50 handhelds
- [ ] Volledige Dolphin/PPSSPP/NetherSX2 configuratie-import via UI
- [ ] Save state cloud sync
- [ ] Mobiele web interface

---

## Bijdragen

Bijdragen zijn welkom, met name voor:

1. **Hardware profielen** — Heb je een chipset die nog ontbreekt? Open een PR met een nieuw item in `config/hardware_profiles/chipsets.json`
2. **Controller configs** — Apparaat-specifieke tweaks voor bekende handhelds (Retroid, Odin, AyaNeo, Anbernic)
3. **BIOS hashes** — Aanvullingen op de MD5-database in `backend/core/bios/checker.py`
4. **Vertalingen** — AI support kennisbank in extra talen

**Code style:** Black + Ruff voor Python, ktlint voor Kotlin.

---

## Licentie

MIT License — zie `LICENSE` voor details.

> EmuFlow distribueert geen ROMs, BIOS-bestanden of gepatenteerde software.
> Alle emulators waarnaar verwezen wordt zijn open source of vrij beschikbaar.

---

*Gebaseerd op best practices van [Retro Game Corps](https://retrogamecorps.com) en [TechDweeb](https://www.youtube.com/@TechDweeb).*
