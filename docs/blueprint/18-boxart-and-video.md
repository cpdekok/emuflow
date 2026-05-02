# Blueprint 18 — Boxart en gameplay-video tijdens browsen

Status: ontwerp, fase 1
Owner: PM/Eng/UX/Legal-stem
Refs: doc 11 (vault), doc 17 (rom-library)

## Probleem

Bij het bladeren door de ROM-bibliotheek wil de gebruiker:

- Boxart per game zien (front-cover)
- Een korte gameplay-video zien tijdens hover/selecteer

De gekozen frontend-launcher levert dit soms al, soms niet. EmuFlow moet:

1. Detecteren of de actieve frontend dit zelf afhandelt — dan **niets** doen
2. Anders: ontbrekende media ophalen of een overlay tonen die de media bijlevert

## Niet-doel

- Geen vervanging worden van bestaande launchers (Daijisho, ES-DE, Pegasus)
- Geen eigen media-database hosten (daar zijn ScreenScraper, TheGamesDB, LaunchBox al voor)
- Geen zware media-redistributie via onze server (auteursrecht-risico, hostingkosten)

## Stemmen

- **PM**: "We willen geen wiel opnieuw uitvinden. Maar voor users die geen ScreenScraper-account hebben moet er iets werken zonder gedoe."
- **Eng**: "Capability-detectie eerst — heel veel werk vermijden door te checken wat de actieve frontend al doet."
- **UX**: "Als wij iets tonen moet het tijdens browsing en niet bij elke klik vertraging geven. Pre-caching is verplicht."
- **Legal**: "Boxart is geclaimd auteursrechtelijk materiaal van uitgevers. ScreenScraper en TheGamesDB hebben dit afgedekt onder hun eigen voorwaarden — wij kunnen verwijzen, niet zelf hosten of distribueren."

## Frontend-capability matrix

| Launcher | Boxart auto | Video auto | Bron | Conclusie EmuFlow-rol |
|---|---|---|---|---|
| **Daijisho** | Ja, streaming | Ja, streaming uit eigen CDN | TapiocaFox-server | Niets doen |
| **ES-DE** | Ja, met ScreenScraper-account | Ja, met ScreenScraper-account | ScreenScraper.fr | Detecteren of media-folder bestaat; als niet → setup-link |
| **Pegasus** | Alleen handmatig (`media/<game>/boxFront.png`) | Idem (`video.mp4`) | Geen | Pre-fill-tool aanbieden via Skraper-instructies |
| **Cocoon** | Beperkt | Nee | TheGamesDB | Overlay aanvullen |
| **AYASpace** | Via AYANeo data manager | Nee | AYANEO | Overlay aanvullen |
| **GoRetroid launcher** | Ja, vendor-curated | Beperkt | GoRetroid-CDN | Niets doen |
| **Native Android (geen launcher)** | Nee | Nee | n.v.t. | Eigen overlay vereist |

## Architectuur

```
LauncherDetector  →  CapabilityProbe  →  MediaResolver  →  OverlayService
   (welke app)      (wat doet die al)    (waar zoeken)    (UI render)
```

### `LauncherDetector`

Stelt vast welke frontend op dit moment de "default" is voor de gebruiker.
Strategie:

1. Lees `PackageManager.queryIntentActivities` voor `Intent.ACTION_MAIN` met
   category `LAUNCHER_HOME`
2. Match tegen bekende package-namen:

| Package | Launcher |
|---|---|
| `com.magneticchen.daijishou` | Daijisho |
| `org.es_de.frontend` | ES-DE |
| `org.pegasus_frontend.android` | Pegasus |
| `tv.cocoon.app` | Cocoon |
| `com.ayaneo.ayaspace` | AYASpace |
| `com.retroid.launcher` | Retroid Launcher |

3. Als geen match: status `unknown_launcher`

### `CapabilityProbe`

Voor de gedetecteerde launcher: stel vast of er al media-bestanden bestaan
voor de huidige ROM-set:

- **Daijisho**: heeft eigen DB; we vragen niet, we accepteren de status
  `streamed` en doen niets
- **ES-DE**: check `~/ES-DE/downloaded_media/<system>/box/<game>.png` en
  `videos/<game>.mp4`
- **Pegasus**: check `<rom-dir>/media/<game>/boxFront.png` en `video.mp4`
- **Cocoon / AYASpace**: vendor-specifieke paden (best effort)
- **Unknown**: geen check, alle media wordt door overlay verzorgd

### `MediaResolver`

Zoekt boxart en video voor een gegeven ROM. **Wij hosten niets zelf.**

**Strategie (in volgorde):**

1. **Lokale media** uit launcher-eigen folder (zie CapabilityProbe)
2. **EmuFlow-archive** in `/sdcard/EmuFlow_Media/<platform>/<game-hash>/` —
   pre-existing assets die de gebruiker zelf heeft geplaatst
3. **Externe scraper-link** (deeplink, niet auto-fetch):
   - ScreenScraper deeplink met game-hash
   - TheGamesDB.net deeplink
4. **Lege staat** met "Open scraper"-button die de gebruiker naar de
   juiste tool leidt (Skraper / ARRM / ScreenScraper-web)

In fase 1 doen we **geen automatische media-download**. Reden: legal/auteursrecht
+ daily-quota's bij scrapers + bandbreedte-overlast voor gebruiker.

In fase 2 overwegen we een opt-in "fetch via my ScreenScraper account" flow,
waar de gebruiker zijn eigen credentials invult en we gebruiken zijn quota.

### `OverlayService` (fase 2-werk, fase 1: design only)

Als de gekozen launcher geen videos toont, biedt EmuFlow een **transparante
overlay** die boven de launcher rendert:

- Detecteert focus-changes via Accessibility-service (OPT-IN, met duidelijke uitleg)
- Toont in onderhoek video-preview van het gehighlighte spel
- Latentie-target: < 150 ms van highlight tot frame-1

Dit vereist:
- `BIND_ACCESSIBILITY_SERVICE` permissie
- Expliciete user opt-in met "wat zien we wel/niet" disclosure
- Privacy-document update: deze overlay leest scherm-content, alleen voor
  game-titel-extractie, niets verlaat het device

## Fase 1 scope (strikt)

**Wat we wel bouwen:**

- `LauncherDetector` — onderdeel van Android Agent
- `CapabilityProbe` — basis-paden voor Daijisho, ES-DE, Pegasus
- `MediaResolver` zonder externe fetch — leest alleen lokale folders
- Setup-wizard stap 6 **"Boxart en video"**:
  - Toont per launcher wat al werkt
  - Geeft installatie-instructies voor Skraper / ARRM voor wie zelf wil scrapen
  - Linkt naar ScreenScraper account-aanmaak
  - **Doet zelf niets dat naar het internet gaat**

**Wat we niet bouwen in fase 1:**

- Automatische media-fetching
- Eigen scraper-server
- Accessibility-overlay (fase 2)
- Eigen launcher

## Data-modellen

```kotlin
enum class LauncherKind {
    DAIJISHO, ES_DE, PEGASUS, COCOON, AYASPACE, RETROID_LAUNCHER, UNKNOWN
}

data class LauncherInfo(
    val packageName: String?,
    val kind: LauncherKind,
    val isDefault: Boolean,
    val supportsBoxartAuto: Boolean,
    val supportsVideoAuto: Boolean
)

data class MediaCoverage(
    val totalRoms: Int,
    val withBoxart: Int,
    val withVideo: Int,
    val launcherKind: LauncherKind,
    val mediaSourcePath: String?  // bijv. "/sdcard/ES-DE/downloaded_media"
)
```

## Privacy en legal

- We **embedden of distribueren** geen boxart of videos
- We **deeplinken** naar bestaande, gerenommeerde scraper-services
- Geen game-titels naar onze servers — capability-probe is volledig lokaal
- Telemetrie ontvangt alleen `MediaCoverage` aggregaten (counts, niet titels)

## Acceptatiecriteria fase 1

- LauncherDetector identificeert correct minstens Daijisho, ES-DE, Pegasus,
  AYASpace, Retroid Launcher
- CapabilityProbe levert correcte coverage-percentages voor minstens
  ES-DE en Pegasus
- Setup-wizard stap 6 toont per launcher een actie-vriendelijk volgend-stappen-blok
- Geen netwerkverkeer naar scraper-services vanuit de Agent in fase 1

## Open vragen

- Wil de gebruiker een keuze-scherm "welke launcher gebruik ik" of accepteren we de
  Android default-launcher als bron-of-truth?
- Hoe omgaan met meerdere launchers tegelijk geïnstalleerd (Daijisho + ES-DE)?
- Moet de overlay (fase 2) ook werken in Daijisho's lijstweergave waar
  videos al ingebouwd zijn (concurrentie of complement)?
