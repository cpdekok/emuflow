---
name: termijnbewaking
description: Signaleert naderende passeerdata, verlopen offertes en stilliggende dossiers uit een gepseudonimiseerde dossierexport (CSV). Trap 1 — invoer mag geen persoonsgegevens bevatten.
---

# Termijnbewaking (trap 1)

Analyseer een gepseudonimiseerde dossierexport en lever een geprioriteerd
actielijstje voor de komende weken.

## Stap 1 — invoer vinden en valideren

1. Zoek in `data/inbox/` naar het meest recente `*.pseudo.csv`-bestand.
   Is er alleen een ruwe export (zonder `.pseudo.`), open die dan NIET verder
   dan de kopregel.
2. Controleer de kopregel op persoonsgegevens-kolommen: naam, voornaam,
   achternaam, adres, woonplaats, postcode, e-mail, telefoon, BSN,
   geboortedatum, IBAN (ook Engelse varianten). Bij een treffer: **stop**,
   verwerk het bestand niet, en meld:
   - welke kolommen het probleem zijn;
   - dat eerst `python3 scripts/pseudonimiseer.py data/inbox/<bestand>`
     gedraaid moet worden;
   - dat het resultaat (`*.pseudo.csv`) daarna wél verwerkt kan worden.
3. Verwachte kolommen (namen mogen afwijken; herken op betekenis):
   dossiernummer, dossiertype, status, datum offerte, datum laatste
   activiteit, geplande passeerdatum, behandelaar(scode). Ontbrekende
   kolommen zijn geen blokkade — rapporteer welke signalen daardoor
   vervallen.

## Stap 2 — signaleren

Gebruik de datum van vandaag. Signaleer per dossier:

| Signaal | Criterium | Prioriteit |
|---------|-----------|------------|
| Passeerdatum nadert | binnen 14 dagen | Hoog (binnen 7 dagen: Urgent) |
| Passeerdatum verstreken | in het verleden, status niet gepasseerd/gesloten | Urgent |
| Offerte verlopen | offerte > 30 dagen oud, status nog offerte | Middel |
| Dossier ligt stil | laatste activiteit > 60 dagen, status open | Middel (> 120 dagen: Hoog) |
| Datum ontbreekt | open dossier zonder passeerdatum én zonder recente activiteit | Laag |

## Stap 3 — rapporteren

Schrijf `data/uitvoer/termijnrapport-JJJJ-MM-DD.md` met:

1. **Samenvatting** — drie tot vijf zinnen: totaal aantal dossiers,
   aantal signalen per prioriteit, wat vandaag aandacht vraagt.
2. **Actielijst** — tabel gesorteerd op prioriteit, daarna datum:
   dossiernummer, type, signaal, relevante datum, voorgestelde actie.
3. **Trends** — alleen als er iets opvalt (stapeling bij één behandelaar-
   code, oplopende doorlooptijden). Geen vergezochte patronen.
4. **Datakwaliteit** — ontbrekende kolommen of onbruikbare datums.

Gebruik uitsluitend dossiernummers en codes — nooit namen, ook niet als er
onverhoopt toch één in de data staat (meld dat dan onder Datakwaliteit,
zonder de naam te herhalen).

Sluit af met een korte weergave van de samenvatting en het pad van het
rapport in de chat.
