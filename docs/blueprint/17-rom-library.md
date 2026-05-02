# Blueprint 17 — ROM-library: preserve, dedupe, taalfilter

Status: ontwerp, fase 1
Owner: PM/CTO/Eng/UX/Legal-stem
Refs: doc 09 (clean-slate), doc 11 (vault), doc 15 (auto-install), doc 18 (boxart/video)

## Probleem

Sommige Android-handhelds worden geleverd met voorgeïnstalleerde games op de
interne opslag of microSD. Voorbeelden:

- GoRetroid / Retroid Pocket-varianten met `/games/download/` op SD
- Anbernic RG-serie met vendor-launcher en eigen ROM-mappen
- AYANEO met AYASpace en data-manager (bevat geen ROMs by default, maar de
  gebruiker kan eigen content op `/games/` plaatsen voordat ze EmuFlow draaien)
- Tweedehands devices met content van de vorige eigenaar

EmuFlow's clean-slate flow (doc 09) verwijdert vendor-shells. Daarbij mag
**onder geen enkele omstandigheid** een ROM-bestand verloren gaan. ROMs zijn
voor de gebruiker waardevol en vaak onvervangbaar.

Daarnaast wil de gebruiker de bibliotheek kunnen opschonen:

1. **Duplicaten** — dezelfde game in meerdere regio's of dump-versies
2. **Taal-overdaad** — niet-Engels/niet-Nederlands waar de gebruiker geen affiniteit mee heeft
3. **Prullenbak-bestanden** — `.txt`, `.nfo`, `.url` die geen game zijn

## Niet-doel

- Geen ROM-content naar onze servers — alles blijft lokaal (privacy-eis doc 11)
- Geen automatische verwijdering — alleen review-flow met expliciete bevestiging
- Geen ROM-validatie / no-intro-dat matching in fase 1 (eventueel fase 2)
- Geen cloud-sync van ROM-library

## Stemmen

- **PM**: "Preserve is non-negotiable. Dedupe + taalfilter zijn premium-features die later achter een paywall kunnen, fase 1 als preview-functie."
- **CTO**: "Hash-based dedupe is goedkoop. Taalheuristiek op filename is fragiel maar werkt voor 80 % van No-Intro/Redump-naamgeving."
- **UX**: "Drie groepen in de review-UI: zeker dupes, waarschijnlijk dupes, taal-kandidaten. Niets wordt gemarkeerd als 'auto-delete'."
- **Legal**: "We kopiëren geen ROMs. Hashes blijven lokaal. Geen probleem."
- **Eng**: "Scan moet incrementeel kunnen — een 256 GB SD opnieuw scannen na 1 nieuwe game mag geen 10 minuten duren."

## Architectuur

```
ROMScanner  →  RomFingerprintIndex  →  LibraryReconciler  →  Review UI
 (file walk)    (hash + metadata)      (preserve-aware)     (user choice)
```

### `ROMScanner`

Vindt ROM-bestanden in alle relevante locaties:

**Locatie-bronnen (in volgorde van prioriteit):**

1. `Environment.getExternalStorageDirectory()` — interne `/sdcard/`
2. `getExternalFilesDirs(null)` — extra mounts incl. microSD
3. Bekende vendor-paden uit `VendorRomPathRegistry`:
   - `/games/download/` (Retroid)
   - `/storage/emulated/0/Roms/` en `/Roms/`
   - `/sdcard/ROMS/` en `ROMs/`
   - `/games/` (GoRetroid, Anbernic-varianten)
   - `Android/data/com.retroarch/files/downloads/` etc.
4. User-toegevoegde paden (fase 2)

**Extensie-mapping per platform:** uit `RomExtensionRegistry` (zie hieronder).

**Performance:**
- Multi-threaded directory walk met `Files.walk(path).parallel()`
- SHA1 hash (sneller dan SHA256 voor dedupe; SHA256 blijft voor vault)
- Incremental scan: persisteer mtime + size per pad in SQLite,
  hash alleen herberekenen als mtime/size veranderde

### `RomFingerprintIndex`

Lokale SQLite-tabel `rom_fingerprints`:

| Kolom | Type | Beschrijving |
|---|---|---|
| id | INTEGER PK | autoincrement |
| absolute_path | TEXT UNIQUE | volledig pad |
| size_bytes | INTEGER | grootte |
| mtime_ms | INTEGER | last modified |
| sha1 | TEXT | hash van inhoud (zonder header voor sommige formaten) |
| platform | TEXT | NES, SNES, PSX, ... |
| filename_normalized | TEXT | basis voor dedupe-naammatching |
| region_tags | TEXT | komma-gescheiden: USA,EUR,JPN |
| language_tags | TEXT | komma-gescheiden: En,Fr,De |
| dump_flags | TEXT | komma-gescheiden: GoodTool flags |
| is_preinstalled | INTEGER | 1 = aanwezig vóór EmuFlow-install |
| first_seen_at | INTEGER | eerste scan-timestamp |
| last_seen_at | INTEGER | meest recente scan |

### `LibraryReconciler`

Levert vier **lijsten** op aan de UI; **niets wordt verwijderd zonder explicit user action**.

#### 1. Preserve-set
Alle bestanden waar `is_preinstalled = 1` of die binnen de eerste 24 uur na
agent-install gezien zijn. Deze set wordt **nooit** door clean-slate of
auto-install aangeraakt. Een uninstall van EmuFlow laat deze bestanden ongemoeid.

#### 2. Exact-duplicates
`GROUP BY sha1 HAVING COUNT(*) > 1`. Toont één-op-één gelijke bestanden
ongeacht naam/locatie. UI biedt: "Behoud kortste pad", "Behoud op SD",
"Behoud preinstalled", per-rij keuze.

#### 3. Probable-duplicates
Naam-gebaseerde matching met heuristiek:

```
strip_region_tags(filename) + strip_dump_flags(filename) + lower
```

Bijvoorbeeld:

```
"Super Mario Bros. (USA).nes"   → super mario bros
"Super Mario Bros. (Europe).nes" → super mario bros
"Super Mario Bros. (Japan) [!].nes" → super mario bros
```

Alle drie matchen op normalized name, ondanks verschillende SHA1. UI toont
ze gegroepeerd; gebruiker kiest welke regio('s) te behouden.

#### 4. Language-candidates
Filenames met taal-tag waar **geen** Engelse/Nederlandse variant bekend is:

```
"Final Fantasy VI (Japan).sfc"  → Ja-only, geen En-versie aanwezig
"Chrono Trigger (Japan).sfc"    → Ja, MAAR (USA).sfc bestaat → niet flaggen voor deletion
                                   wel beschikbaar voor "verberg niet-EN" filter
```

Gebruiker zet eigen voorkeurstalen (default: En, Nl). De UI splitst:

- **Verberg in launcher** (default-aanrader, niet-destructief)
- **Verplaats naar archive-map** (`/sdcard/EmuFlow_Archive/`)
- **Verwijder** (alleen na expliciete bevestiging + 7-daagse wachtperiode in fase 2)

Voor fase 1 ondersteunen we alleen **Verberg in launcher** + **Archive-verplaatsing**.

### `VendorRomPathRegistry`

Statische lijst van bekende vendor-locaties per device-fabrikant:

```kotlin
data class VendorRomPath(
    val vendor: String,                    // "Retroid", "Anbernic", "GoRetroid", "AYANEO"
    val relativePath: String,              // "games/download" (van externe-storage-root)
    val description: String,
    val typicallyPreinstalled: Boolean
)
```

Wordt gebruikt door `ROMScanner` om de juiste paden te bezoeken én door
clean-slate (doc 09) om vendor-content te detecteren zonder aan te raken.

### `RomExtensionRegistry`

Per emulator-platform een lijst van geldige extensies:

| Platform | Extensies |
|---|---|
| NES | nes, fds, unf |
| SNES | sfc, smc, swc, fig |
| GB/GBC | gb, gbc, sgb |
| GBA | gba |
| N64 | n64, z64, v64, ndd |
| GameCube | iso, gcm, ciso, rvz, wbfs |
| Wii | iso, wbfs, rvz, wad |
| PSX | bin, cue, chd, m3u, pbp, iso, ecm |
| PS2 | iso, chd, cso, gz |
| PSP | iso, cso, pbp, chd |
| Saturn | bin, cue, chd, mds, ccd |
| Dreamcast | gdi, cdi, chd, cue |
| NDS | nds, zip |
| 3DS | 3ds, cci, cxi, cia |
| Genesis/MD | gen, md, smd, bin |
| MAME | zip, 7z |

Zip- en 7z-files worden **niet uitgepakt** voor hashing — we hashen het
archief zelf (matcht de manier waarop emulators ze laden).

## Filename-parser

Gebruikt door zowel dedupe als language-filter. Patroon:

```
<title> [(<tag>)]* [\[<flag>\]]* .<ext>
```

Tags binnen `()`:

- **Region**: USA, Europe, Japan, World, Asia, Korea, Brazil, ...
- **Language**: En, Fr, De, Es, It, Ja, Nl, ...
- **Variant**: Beta, Proto, Demo, Rev 1, v1.1
- **Compilation**: Disc 1, Side A

Flags binnen `[]` (GoodTool-stijl):

- `!` = perfect dump
- `b` = bad dump
- `h` = hack
- `p` = pirate
- `T+` / `T-` = translation patch

Onbekende tags worden gepreserveerd in de geparseerde struct.

## User-flow (Setup-wizard, stap 5)

Na clean-slate biedt de wizard een nieuwe pagina **"Bibliotheek opschonen"**
met drie tabs:

1. **Behoud beschermd** (read-only) — toont preinstalled-set met "Deze blijven onaangeraakt"
2. **Duplicaten** — exact + probable, met per-groep "wat te behouden"
3. **Talen** — voorkeuren in/uit, archief vs verbergen

Geen verwijdering zonder een tweede confirmatie-modal.

## Privacy en veiligheid

- ROM-hashes blijven **lokaal** in `/data/data/com.emuflow.agent/databases/`
- Geen filenames, hashes of paden naar telemetrie
- Telemetrie ontvangt alleen aggregaten: `rom_count_by_platform`, `duplicate_count`,
  `archive_count` — als opt-in (default: niet meegestuurd)
- Bij agent-uninstall: hash-database wordt verwijderd, ROMs blijven staan

## Telemetrie (opt-in, anoniem)

Alleen geaggregeerde counters in heartbeat:

```json
{
  "rom_library_stats": {
    "total_count": 423,
    "by_platform": {"snes": 80, "psx": 22, "gba": 95},
    "duplicate_groups": 12,
    "language_filtered_visible": 380,
    "archive_count": 31
  }
}
```

## Open vragen

- Moeten we no-intro DAT-files bundelen voor preciezere matching? (kosten: ~50 MB extra APK-grootte)
- Hoe omgaan met multi-disc PSX/PS2 games waar elke disc apart hasht maar als unit getoond moet worden?
- Wanneer een gebruiker een ROM in archive plaatst en later de SD wisselt: archive-map mee-migreren of opnieuw aanmaken?
- microSD-volumelabel-wijziging detecteren zodat indexen niet ongeldig worden?

## Acceptatiecriteria fase 1

- ROMScanner detecteert minimaal 95 % van bekende ROMs in vendor-paden van Retroid, Anbernic, GoRetroid, AYANEO op basis van extensie + locatie
- Hash-tijd voor 256 GB SD met ~5000 ROMs onder 5 minuten op Snapdragon 865 (incremental: < 30 s)
- Geen enkel ROM-bestand wordt automatisch verwijderd of verplaatst
- Preserve-set is bestand tegen clean-slate, auto-install en agent-uninstall
- Filename-parser behaalt > 90 % juiste regio/taal-extractie op No-Intro-genaamde ROMs
