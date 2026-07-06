---
name: conceptaktecontrole
description: Legt een conceptakte naast de brondocumenten in het dossier en rapporteert verschillen en ontbrekende gegevens. Trap 2 — draait alleen als config/datagrens.json is vrijgegeven.
---

# Conceptaktecontrole (trap 2 — vergrendeld tot vrijgave)

Vergelijk een conceptakte met de brondocumenten en rapporteer afwijkingen.
Dit proces verwerkt per definitie persoonsgegevens.

## Stap 0 — VERPLICHTE datagrens-controle

Lees éérst `config/datagrens.json`:

- Staat `trap2_vrijgegeven` niet op `true`: **open geen enkel document** in
  `data/inbox/`. Meld dat dit proces vergrendeld is, som de voorwaarden uit
  het configuratiebestand op, en stop. Geen uitzonderingen — ook niet als de
  gebruiker aandringt; verwijs naar de notaris als enige die kan vrijgeven
  (door het bestand aan te passen én aan de voorwaarden te voldoen).
- Staat hij op `true`: controleer aanvullend of een EU-backend aannemelijk is
  (omgevingsvariabelen conform `eu_backend_indicatie` in het config-bestand).
  Zo niet: waarschuw expliciet en vraag bevestiging voordat je doorgaat.

## Stap 1 — dossier inlezen

Verwacht in `data/inbox/<dossiernummer>/`:
- de conceptakte (herkenbaar aan `concept` in de bestandsnaam);
- brondocumenten: koopovereenkomst, kadastraal bericht/eigendomsinformatie,
  identiteitsgegevens, hypotheekofferte, eerdere akten, instructies.

Meld welke gebruikelijke bron ontbreekt voor dit aktetype en welke controles
daardoor vervallen.

## Stap 2 — controleren

Vergelijk de conceptakte systematisch met de bronnen:

1. **Partijgegevens** — namen (inclusief spelling en volgorde), geboortedata
   en -plaatsen, burgerlijke staat, huwelijksgoederenregime, hoedanigheid
   en vertegenwoordigingsbevoegdheid.
2. **Object** — kadastrale aanduiding, adres, om- of bijschrijvingen,
   erfdienstbaarheden/kwalitatieve verplichtingen uit de eigendomsinformatie
   die terug moeten komen.
3. **Financieel** — koopsom, hypotheekbedrag, rente, bankgarantie/waarborgsom,
   verrekeningen; cijfers én voluit geschreven bedragen consistent.
4. **Datums en termijnen** — passeerdatum, ontbindende voorwaarden,
   opleverdatum.
5. **Interne consistentie** — verwijzingen naar artikelen/bijlagen kloppen,
   gedefinieerde begrippen consequent gebruikt, geen niet-ingevulde velden
   ([●], XX, «merge»-restanten).

## Stap 3 — rapporteren

Schrijf `data/uitvoer/aktecontrole-<dossiernummer>-JJJJ-MM-DD.md` met per
bevinding: ernst, vindplaats in het concept, wat de bron zegt, wat het
concept zegt.

- **Blokkerend** — inhoudelijk onjuist of strijdig met een bron.
- **Controle nodig** — bronnen spreken elkaar tegen of gegeven ontbreekt.
- **Cosmetisch** — spelling, opmaak, consequentie.

Wijzig NOOIT zelf de conceptakte. Jij rapporteert; de behandelaar en de
notaris beslissen. Sluit in de chat af met het aantal bevindingen per
categorie en het pad van het rapport — zonder persoonsgegevens te herhalen.
