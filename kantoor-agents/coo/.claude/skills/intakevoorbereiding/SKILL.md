---
name: intakevoorbereiding
description: Maakt uit aangeleverde dossierstukken een intakeoverzicht, een lijst van ontbrekende stukken en een vragenlijst voor de bespreking. Trap 2 — draait alleen als config/datagrens.json is vrijgegeven.
---

# Intakevoorbereiding (trap 2 — vergrendeld tot vrijgave)

Bereid een intakebespreking voor op basis van de aangeleverde stukken.
Dit proces verwerkt per definitie persoonsgegevens.

## Stap 0 — VERPLICHTE datagrens-controle

Identiek aan `/conceptaktecontrole`: lees éérst `config/datagrens.json`.
Staat `trap2_vrijgegeven` niet op `true`, open dan geen enkel document,
meld de vergrendeling met de voorwaarden, en stop — zonder uitzondering.
Staat hij op `true` maar is een EU-backend niet aannemelijk uit de
omgevingsvariabelen: waarschuw en vraag bevestiging.

## Stap 1 — stukken inlezen

Verwacht in `data/inbox/<dossiernummer>/` een set aangeleverde stukken,
bijvoorbeeld: koopovereenkomst, identiteitsbewijzen, hypotheekofferte,
huwelijkse voorwaarden/partnerschapsvoorwaarden, verklaring van erfrecht,
oprichtingsakte/KvK-uittreksel, taxatierapport, instructie- of
aanvraagmail. Stel eerst vast wélk soort zaak dit is (levering, hypotheek,
testament, huwelijkse voorwaarden, oprichting, nalatenschap) en pas de
rest daarop aan.

## Stap 2 — drie producten maken

Schrijf `data/uitvoer/intake-<dossiernummer>-JJJJ-MM-DD.md` met:

### 1. Intakeoverzicht
- **Partijen** — wie, in welke hoedanigheid, burgerlijke staat/regime,
  vertegenwoordiging; bijzonderheden (minderjarigheid, volmacht, buitenlands
  ID, taalbarrière).
- **Zaak** — object of onderwerp, kern van de gewenste rechtshandeling.
- **Financieel** — bedragen, financiering, herkomst middelen voor zover
  uit de stukken blijkt.
- **Signalen** — Wwft-aandachtspunten (ongebruikelijke constructie,
  herkomst middelen onduidelijk, PEP-indicatie), tegenstrijdigheden tussen
  stukken, tijdsdruk. Signaleer alleen; de Wwft-beoordeling zelf is aan
  het kantoor.

### 2. Ontbrekende stukken
Wat gebruikelijk nodig is voor dit zaakstype maar niet is aangeleverd,
met per stuk waarom het nodig is en bij wie het opgevraagd moet worden.

### 3. Vragenlijst voor de bespreking
Concrete vragen die de notaris tijdens de intake moet stellen: keuzes die
de cliënt nog moet maken, onduidelijkheden in de stukken, wilscontrole-
aandachtspunten. Gesorteerd: eerst wat de voortgang blokkeert.

## Grenzen

- Geen conceptteksten van akten opstellen in dit proces.
- Geen juridisch eindoordeel; formuleer twijfels als vraag aan de notaris.
- In de chat alleen een korte samenvatting en het rapportpad noemen —
  persoonsgegevens blijven in het rapport, niet in de chat.
