# 11 — Save Vault en Save-Management

Status: Draft v1 — fase 1 P0-feature in v0-vorm. Besluit COO 2026-04-27 na multi-disciplinair overleg (CTO, UX, Legal, PM).

## Context

Savestates zijn de meest-gebruikte feature van retrogaming en tegelijk de meest-foutgevoelige: verkeerde slot, overschreven, kwijt na emulator-update, niet compatibel tussen versies. Geen enkele bestaande Android-launcher (Daijisho, ES-DE, Beacon) raakt savestates aan. Dit is onontgonnen terrein en een potentiële differentiator.

Founder zelf heeft op Odin 2 ervaren wat er fout gaat (saves kwijt, slot-verwarring). Save Vault adresseert dit "dummy-proof" zonder de native emulator-systemen te vervangen.

## Doelen

1. Geen save mag verloren gaan zonder gebruikers-actie
2. Backups gebeuren automatisch en onzichtbaar
3. Werkt cross-emulator zonder emulator-internals aan te raken
4. Foundationele datalaag die later (fase 2-3) UI en cloud-sync ondersteunt

## Niet-doelen fase 1

- Unified savestate-overlay UI (fase 2)
- Pre-overschrijf bevestiging (fase 2, alleen bij restore-flow)
- Cross-device sync (fase 3, alleen zero-knowledge E2EE)
- Eigen auto-save trigger via emulator-hooks (fase 2)
- Versie-tracking met compatibiliteitswaarschuwingen (fase 2)
- Auto-thumbnail van eerste game-frame (fase 2, nu fallback naar quick-screenshot)

## Architectuur fase 1 (v0)

### Save Vault v0 — wat wel

**1. FileObserver-service**

Achtergrondservice die de save- en state-directories van bekende emulators monitort:

| Emulator | Save-directory (typisch) |
|---|---|
| PPSSPP | `/sdcard/PSP/SAVEDATA/`, `/sdcard/PSP/PPSSPP_STATE/` |
| Dolphin | `/sdcard/Dolphin Emulator/StateSaves/`, `/sdcard/Dolphin Emulator/GC/<region>/Card A/` |
| DuckStation | `/sdcard/Android/data/com.github.stenzek.duckstation/files/memcards/`, `/files/savestates/` |
| AetherSX2 | `/sdcard/Android/data/xyz.aethersx2.android/files/sstates/`, `/files/memcards/` |
| RetroArch | `/sdcard/RetroArch/saves/`, `/sdcard/RetroArch/states/` |

Paden zijn configureerbaar per device-profiel (sommige vendor-builds zetten dit elders).

**2. Vault-locatie en structuur**

```
/sdcard/EmuFlow_Vault/
  <emulator_package>/
    <game_id_or_filename_hash>/
      <slot_or_filename>/
        2026-04-27T10-23-15.state
        2026-04-27T10-15-02.state
        ...
```

Rolling buffer: maximaal 10 versies per slot/bestand.

**3. Integriteit**

- SHA256 over elke vault-kopie
- Bij elke restore (fase 2): hash valideren, waarschuwen bij corruptie

**4. Koppeling**

CTO-advies overgenomen: ROM-hash is niet de primaire sleutel.

- Primaire koppeling: `package + save-path + filename/slot + device-local game-record`
- Secundaire fingerprint: SHA1 van eerste 1MB van ROM (alleen lokaal)
- Extra metadata: bestandsgrootte, modified time, optioneel display-name

Bij gelijke hash op verschillende ROM-bestanden: behandel als "waarschijnlijk dezelfde game", niet als harde identiteit.

**5. UI in fase 1**

Geen unified overlay. Wel:

- Eén knop in Instellingen: "Open Save Vault map" (opent bestandsbeheerder op locatie)
- Statuslabel: "Laatste backup: vandaag 14:23"
- Bij backup-fout: één rustige notificatie met één actie ("Ruimte vrijmaken" of "Toestemming geven")

UX-besluit: geen aparte "Save Vault"-bestemming in de hoofdnavigatie, integratie blijft onzichtbaar in fase 1.

## Resume Last Game (gerelateerd, lichte vorm)

**Niet hetzelfde als auto-save**. EmuFlow doet zelf geen save-trigger. Wij vertrouwen op de native savestate-functionaliteit van de emulators (PPSSPP, Dolphin etc. hebben dit al).

Wat EmuFlow wel doet:

- Onthoudt laatst-gespeelde game + emulator + core
- Eén knop op homescreen: "Verder met [game]"
- Bij launch: emulator opent op laatste savestate-slot (vraagt aan emulator zelf)

Subtiele exit-detectie: wanneer emulator-process eindigt (via `ActivityManager`), registreer "laatst gespeeld". Geen actieve trigger.

## Privacy en juridisch (Legal-besluit)

### Groen — geen actie nodig

- Lokale opslag in `/sdcard/EmuFlow_Vault/`: savestate is geen ROM-content, valt buiten DSA/auteursrecht
- Telemetrie met save-events (frequentie, slot, emulator-package): GDPR art. 6.1.f, mits gepseudonimiseerd

### Geel — toegestaan mits voorwaarden

- ROM-hash (SHA1 eerste 1MB): **strict lokaal**, nooit naar onze servers, nooit in telemetrie
- Thumbnails (fase 2): **strict lokaal**, geen sync naar cloud

### Rood — verboden, ooit

- ROM-hash naar onze cloud of in telemetrie
- Hash-lookup tegen externe titel-databases (No-Intro, Redump, IGDB)
- Cross-device sync zonder zero-knowledge E2EE (fase 3-vereiste)
- Thumbnail-sync naar cloud (geen werkbare auteursrechtexceptie)

### First-run disclaimer (letterlijk uit Legal-advies)

> Over Save Vault
>
> EmuFlow slaat uw savestates op uw eigen apparaat op in /sdcard/EmuFlow_Vault/. EmuFlow ontvangt, verwerkt of kopieert geen spelbestanden (ROMs), BIOS-bestanden of game-content van of naar onze servers.
>
> Thumbnails en screenshots worden lokaal op uw apparaat bewaard en worden niet gedeeld met EmuFlow.
>
> EmuFlow verzamelt anonieme gebruiksstatistieken (frequentie van opslaan, type emulator). Er worden geen bestands- of spelidentificatoren verstuurd. U kunt telemetrie uitschakelen in Instellingen > Privacy.
>
> U bent zelf verantwoordelijk voor het rechtmatige gebruik van spelbestanden. EmuFlow stelt geen ROMs of BIOS-bestanden beschikbaar.

## Telemetrie-uitbreiding

Toe te voegen aan heartbeat (geen ROM-info):

```json
{
  "save_events_24h": {
    "saves_total": 47,
    "saves_per_emulator": {
      "ppsspp": 12,
      "dolphin": 8,
      "retroarch": 27
    },
    "vault_size_mb": 124,
    "vault_versions_total": 312,
    "backup_failures_24h": 0
  }
}
```

## Implementatievolgorde (CTO-advies)

1. Permission-bundel, storage-check, battery-saver-waarschuwing (Setup-QoL eerst)
2. Handmatige backup en restore voor één emulator end-to-end (PPSSPP als pilot)
3. FileObserver + rolling buffer + SHA256-integriteitscontrole
4. Uitbreiden naar overige ondersteunde emulators via configureerbare pad-adapters
5. Pre-overschrijf bevestiging bij restore (P1, niet bij auto-backup)
6. Quick-screenshot als aparte QoL en optionele preview-bron (fase 2)

## Fase 2 (na solo-test)

- Unified Save Vault UI: lijst per game, restore-knop, diff-weergave
- Cross-device save-import via USB of lokale netwerkshare
- Pre-overschrijf bevestiging bij restore-flow
- Emulator-versie-tracking met compatibiliteitswaarschuwingen
- Quick-screenshot als preview-bron voor save-thumbnails

## Fase 3+

- Cloud-sync uitsluitend zero-knowledge E2EE
- Conflict-resolutie UI
- Save-export "share je save" als premium-trigger
- Versiegeschiedenis "nooit een save kwijt" als premium-feature

## Pricing-positionering (PM-advies)

Save Vault v0 (lokaal, automatisch) blijft gratis — lock-in haak voor adoptie. Premium-trigger in fase 3: cloud-sync + cross-device restore + versiegeschiedenis-garantie. Architectuur nu al zo opzetten dat splitsing later kan zonder migratie.

## Acceptance criteria fase 1

- Given gebruiker maakt een save in PPSSPP
- When EmuFlow-agent draait met permissions
- Then binnen 5 seconden verschijnt een gestempelde kopie in /sdcard/EmuFlow_Vault/org.ppsspp.ppsspp/<game-id>/<slot>/

- Given vault bevat 10 versies van een slot
- When 11e save wordt gemaakt
- Then oudste versie wordt verwijderd, nieuwste toegevoegd

- Given gebruiker drukt "Verder met [game]"
- When laatst-gespeelde game bekend is
- Then emulator opent direct met die game zonder verdere keuzes

## Implementatie-architectuur (fase 1)

De Save-Vault pipeline in de Android Agent bestaat uit vier lagen:

```
RecursiveFileObserver  →  SaveDebouncer  →  CorruptionGuard  →  VaultManager
     (events)            (clustering)      (filtering)        (copy + hash)
```

1. **RecursiveFileObserver** — wrapper rond `android.os.FileObserver` die ook subdirectories monitort. Op API 29+ moet recursive monitoring expliciet gebouwd worden door per subdir een observer te registreren. Nieuwe directories worden dynamisch toegevoegd via CREATE-events; verwijderde directories triggeren automatische deregistratie.

2. **SaveDebouncer** — emulators schrijven save-bestanden vaak in bursts (tijdelijk bestand, rename, meta-bestand). Per write een vault-kopie maken explodeert de buffer. De debouncer wacht 750 ms na het laatste event op hetzelfde pad voordat hij de pipeline doorzet, met een hard maximum van 5 s om constant-schrijvende swap-bestanden niet eeuwig te blokkeren.

3. **CorruptionGuard** — conservatieve heuristiek om onbruikbare backups te weren:
   - REJECT: zero-byte, < 16 bytes, of bekende temp/lock-extensies (`.tmp`, `.part`, `.swp`, `.lock`)
   - SUSPICIOUS: nieuwe versie < 25 % van laatste goede versie (drastische krimp)
   - OK: anders
   SUSPICIOUS-saves worden in fase 1 wel opgeslagen maar gemarkeerd; in fase 2 krijgen ze een aparte vault-tak en worden ze niet als default-restore aangeboden.

4. **VaultManager** — kopieert naar de rolling buffer, hashet met SHA256, prunet naar `MAX_VERSIONS_PER_SLOT` versies en levert telemetrie-statistieken aan voor heartbeat.

Elke laag is een aparte klasse in `com.emuflow.agent.savevault` zodat ze afzonderlijk te testen zijn (unit-tests komen in fase 2 met JUnit + Robolectric).

## Open vragen

- Werkt FileObserver betrouwbaar op Android 14/15 met scoped storage-beperkingen? — *RecursiveFileObserver toegevoegd; te valideren op eerste device-test*
- Hoe omgaan met emulators die saves naar `Android/data/<package>/` schrijven (vereist Shizuku of MANAGE_EXTERNAL_STORAGE)? — *MANAGE_EXTERNAL_STORAGE is bundle-default; Shizuku-fallback in fase 2*
- Vault op interne opslag of microSD: gebruiker-keuze of auto-detectie van vrije ruimte?
- inotify watch-limiet (typisch 8192 per process op Android) — huidige observer logt waarschuwing boven 4000 watches; te monitoren bij eerste device-test
