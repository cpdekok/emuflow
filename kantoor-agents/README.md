# Kantoor-agents

AI-werkomgevingen voor het notariskantoor, gebouwd op Claude Code. Elke agent is een
map met een eigen rolprofiel (`CLAUDE.md`), eigen skills en eigen datagrenzen.

> **Let op:** deze repository hoort privé te blijven. Er staat bewust géén
> dossierdata in (`data/` is uitgesloten via `.gitignore`), maar de werkwijze
> van het kantoor is intern.

## Wat zit erin

```
kantoor-agents/
└── coo/                        De AI-COO van het kantoor
    ├── CLAUDE.md               Rolprofiel: gedrag, geheimhouding, datagrenzen
    ├── config/datagrens.json   Schakel voor het verwerken van cliëntdata
    ├── .claude/skills/
    │   ├── termijnbewaking/        /termijnbewaking   (trap 1 — gepseudonimiseerd)
    │   ├── conceptaktecontrole/    /conceptaktecontrole (trap 2 — vergrendeld)
    │   └── intakevoorbereiding/    /intakevoorbereiding (trap 2 — vergrendeld)
    ├── scripts/pseudonimiseer.py   Lokale pseudonimisering van CSV-exports
    └── data/
        ├── inbox/              Hier zet je exports en stukken neer
        ├── uitvoer/            Hier verschijnen rapporten
        └── sleutels/           Sleuteltabellen pseudonimisering (blijven lokaal)
```

## Installatie op de Mac Mini

```bash
git clone https://github.com/cpdekok/kantoor-agents.git ~/kantoor-agents
cd ~/kantoor-agents/coo
claude                          # start Claude Code in de COO-rol
```

Claude Code leest automatisch `CLAUDE.md` en de skills. Typ daarna bijvoorbeeld:

```
/termijnbewaking
```

## De datatrappen (AVG / Wna)

De agent werkt met drie datatrappen, vastgelegd in het rolprofiel en afgedwongen
in de skills:

| Trap | Data | Status |
|------|------|--------|
| 0 | Geen cliëntdata (cijfers op kantoorniveau, planning, modellen) | Vrij te gebruiken |
| 1 | Gepseudonimiseerd (dossiernummers, datums — geen persoonsgegevens) | Vrij te gebruiken, ná `pseudonimiseer.py` |
| 2 | Herleidbare cliëntdata (akten, ID's, koopovereenkomsten) | **Vergrendeld** via `config/datagrens.json` |

Trap 2-skills (conceptaktecontrole, intakevoorbereiding) weigeren te draaien
zolang `trap2_vrijgegeven` op `false` staat. Zet die pas op `true` wanneer:

1. Claude Code via een **EU-backend** draait, bijvoorbeeld AWS Bedrock Frankfurt:
   ```bash
   export CLAUDE_CODE_USE_BEDROCK=1
   export AWS_REGION=eu-central-1
   ```
   (of Google Vertex AI in een EU-regio), mét verwerkersovereenkomst;
2. de **DPIA** is uitgevoerd en de verwerking in het **verwerkingsregister** staat;
3. jij als notaris het gebruik verenigbaar acht met de geheimhoudingsplicht (art. 22 Wna).

## Pseudonimiseren van exports (trap 1)

```bash
cd kantoor-agents/coo
python3 scripts/pseudonimiseer.py data/inbox/dossiers.csv
```

Het script verwijdert of codeert persoonsgegevens-kolommen en schrijft:
- `data/inbox/dossiers.pseudo.csv` — veilig aan de agent te geven;
- `data/sleutels/dossiers.sleutel.csv` — de vertaaltabel, **blijft op de Mac Mini**
  (staat in `.gitignore` en gaat nooit naar het model).

## Later toevoegen

- `pa/` — persoonlijke assistent (eigen map, eigen CLAUDE.md, eigen connectors)
- MCP-connectors per rol: `claude mcp add …` in de betreffende map
