# De Herschool — schrijfproject

Zevendelige YA/Adult sci-fi-reeks van Christian de Kok. Nederland, 2028–2035.

Dit is de werkomgeving voor het (her)schrijven van de reeks met Claude Code.

## Structuur

```
herschool/
├── projectbijbel.md      De canon: premisse, personages, stijl, 7-boekenboog
├── canon-log.md          Groeiend logboek van canonfeiten (ontstaat vanzelf)
├── CLAUDE.md             Rolprofiel schrijfassistent (stijl- en canonbewaking)
├── .claude/skills/
│   └── hoofdstuk/        /hoofdstuk — schrijft/herschrijft een hoofdstuk
└── manuscript/
    ├── boek-1/           hoofdstuk-01-titel.md, hoofdstuk-02-...
    └── ...               boek-2 t/m boek-7
```

## Gebruik op de Mac Mini

```bash
cd ~/herschool
claude
```

Daarna bijvoorbeeld:

```
/hoofdstuk boek 1 hoofdstuk 1
```

De assistent leest eerst de projectbijbel, legt een synopsis voor, en
schrijft pas na akkoord. Nieuwe canonfeiten komen automatisch in
`canon-log.md`.

## Openstaand

- **Personages aanvullen**: de bijbel brak in de bronversie af na Sophie;
  het derde hoofdpersonage ("Om…") en eventuele overige personages moeten
  opnieuw worden aangeleverd of uitgewerkt (zie de markering in
  `projectbijbel.md`).
- De oorspronkelijke hoofdstukken zijn niet meegekomen en worden opnieuw
  geschreven — dat is een bewuste keuze.
