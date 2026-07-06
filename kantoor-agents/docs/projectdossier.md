# Projectdossier: AI-agents voor kantoor en privé

Verslag van het ontwerpgesprek (Claude Code-sessie, 6 juli 2026) waarin dit
project is bedacht en gebouwd. Bedoeld als context voor de Claude Code-agent
op de Mac Mini (MM) en voor iedereen die later aan dit project verder werkt.

## 1. Doel en visie

Christiaan (notaris) wil met AI-agents communiceren op twee manieren:

1. **PA** — een persoonlijke assistent voor privézaken (agenda, herinneringen,
   administratie).
2. **AI-COO** — een operationele rechterhand voor het notariskantoor
   (dossierbewaking, kwaliteitscontrole, werkvoorbereiding).

Beide draaien op **Claude Code op de Mac Mini**, elk in een eigen werkmap met
een eigen rolprofiel (`CLAUDE.md`), eigen skills en eigen permissies. De
aansturing gebeurt op afstand; het huidige kanaal is **Telegram via Hermes** —
de Hermes-agent heet **Prometheus**.

## 2. Architectuurbeslissingen

- **Motor**: Claude Code CLI op de MM. Cloudsessies (claude.ai/code) kunnen
  niet rechtstreeks bij de MM; uitwisseling loopt via GitHub. Een websessie
  kan wel naar de MM worden overgenomen met `claude --teleport <session-id>`.
- **Rollen = mappen**: per rol een directory met `CLAUDE.md` (gedrag, grenzen)
  en `.claude/skills/` (vaste werkprocessen als slash-commando's).
- **Connectors**: externe systemen koppelen via MCP-servers (`claude mcp add`),
  per rol apart — vergelijkbaar met "connectors" bij andere AI-diensten, maar
  open standaard en zelf uit te breiden. Op macOS kan daarnaast veel native
  via AppleScript (Mail, Agenda, Contacten, Berichten).
- **Kantoorwerk begint met losse processen**, elk met export/bestandsmap als
  invoer en een rapport als uitvoer. Kantoorsysteem-integratie komt eventueel
  later. Als eerste drie gekozen: termijnbewaking, conceptaktecontrole,
  intakevoorbereiding.
- Alternatieve kanalen naast Telegram (besproken, nog niet gekozen):
  `claude remote-control` + Claude-app, SSH via Tailscale, iMessage-bridge,
  eigen webdashboard op de Agent SDK.

## 3. Compliance (AVG / art. 22 Wna) — de datatrappen

Kernpunt: de CLI draait lokaal, maar het **model draait bij Anthropic**
(standaard VS). Alles wat in de context van een gesprek komt, verlaat dus het
kantoor. Daarom werken de agents met drie datatrappen:

| Trap | Data | Status |
|------|------|--------|
| 0 | Geen cliëntdata (geaggregeerde cijfers, planning, modellen) | Vrij |
| 1 | Gepseudonimiseerd (dossiernummers, datums; geen persoonsgegevens) | Vrij, ná lokaal pseudonimiseren |
| 2 | Herleidbare cliëntdata (akten, ID's, overeenkomsten) | **Vergrendeld** via `coo/config/datagrens.json` |

Trap 2 mag pas open wanneer (a) Claude Code via een **EU-backend** draait
(AWS Bedrock eu-central-1 of Google Vertex AI EU-regio, met
verwerkersovereenkomst), (b) een **DPIA** is uitgevoerd en de verwerking in
het **verwerkingsregister** staat, en (c) de notaris het gebruik verenigbaar
acht met de geheimhoudingsplicht. Aanvullend relevant: de Claude API en
Claude for Work zijn DPA-geschikt (geen training op prompts, EU SCC's);
Zero Data Retention is voor enterprise-API-klanten contractueel afsluitbaar;
Anthropic zelf biedt medio 2026 nog geen EU-inferentie.

## 4. Wat er is gebouwd (map `coo/`)

- **`CLAUDE.md`** — rolprofiel AI-COO: Nederlands, zakelijk, notariële
  vaktermen; geheimhouding en datatrappen als harde regels; rapporten
  schrijven mag zelfstandig, versturen/verwijderen/buiten de map alleen na
  akkoord van de notaris.
- **`/termijnbewaking`** (trap 1) — analyseert een gepseudonimiseerde
  CSV-export: naderende/verstreken passeerdata, verlopen offertes (>30 dgn),
  stilliggende dossiers (>60 dgn). Weigert bestanden met
  persoonsgegevens-kolommen. Rapport naar `data/uitvoer/`.
- **`/conceptaktecontrole`** (trap 2, vergrendeld) — legt conceptakte naast
  brondocumenten: partijgegevens, kadastrale aanduiding, bedragen, datums,
  interne consistentie. Bevindingen: blokkerend / controle nodig / cosmetisch.
  Past de akte nooit zelf aan.
- **`/intakevoorbereiding`** (trap 2, vergrendeld) — maakt uit aangeleverde
  stukken een intakeoverzicht, ontbrekende-stukkenlijst en vragenlijst;
  signaleert Wwft-aandachtspunten zonder zelf te beoordelen.
- **`scripts/pseudonimiseer.py`** — lokaal draaien vóór trap 1-gebruik:
  verwijdert adres/BSN/contact-kolommen, codeert namen (zelfde persoon =
  zelfde code), maskeert BSN's (elfproef) en e-mailadressen in vrije tekst.
  Sleuteltabel blijft in `data/sleutels/` (gitignored). Getest met fictieve
  data; werkt.
- **`data/`** — inbox (invoer), uitvoer (rapporten), sleutels; inhoud gaat
  via `.gitignore` nooit naar GitHub.

## 5. Verhuizing naar eigen repo

Dit project is los van EmuFlow (retro-handheldproject) en is daarom via de
emuflow-branch `claude/claude-code-identification-lf2sap` als transportmiddel
onderweg naar een eigen **privé**repo `cpdekok/kantoor-agents`. De
cloudsessie mocht zelf geen repo aanmaken; Prometheus voert de verhuizing uit
op de MM (repo aanmaken met `gh repo create --private`, pushen, controleren,
en daarna `kantoor-agents/` uit de emuflow-branch verwijderen).

## 6. Vervolgstappen (open)

1. `pseudonimiseer.py` afstemmen op de echte kolomnamen van de
   kantoorsysteem-export en `/termijnbewaking` proefdraaien.
2. **PA-rol** opzetten als tweede map (`pa/`) met eigen CLAUDE.md en
   connectors (agenda, mail).
3. MCP-connectors kiezen en koppelen per rol (Microsoft 365 of Google —
   nog niet vastgesteld welke het kantoor gebruikt).
4. EU-fundament voor trap 2: Bedrock/Vertex-account, verwerkersovereenkomst,
   DPIA, verwerkingsregister; daarna `datagrens.json` vrijgeven.
5. Kanaalkeuze heroverwegen (Telegram/Prometheus behouden, Remote Control
   ernaast, of webdashboard bouwen).
