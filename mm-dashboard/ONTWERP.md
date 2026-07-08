# Ontwerp: MM-Dashboard

Eigen webdashboard op de Mac Mini voor het aansturen van de Claude-rollen
(PA, COO, boek), als structurele opvolger van de chat-bruggen. Versie 0.1,
ter bespreking.

## Waarom een dashboard (naast de bruggen)

De bruggen (Prometheus/Telegram, iMessage, Remote Control) zijn chatvensters:
prima voor opdrachten, maar krap voor wat het PA/COO-model echt nodig heeft:

1. **Meerdere rollen naast elkaar** — één scherm met de PA-, COO- en
   boeksessie, elk met eigen status, zonder prefix-trucs.
2. **Goedkeurflows** — de COO stelt een actie voor (mail versturen, bestand
   verwijderen, iets buiten zijn map), het dashboard toont een kaart met
   context en knoppen [Toestaan] [Weigeren]. Precies wat de notariële
   escalatieregels vragen; in een chatkanaal is dit houtje-touwtje.
3. **Zicht op lopend werk** — live tool-uitvoer, rapporten uit
   `data/uitvoer/` direct leesbaar, gezondheidsstatus van de bruggen.

## Architectuur

```
iPhone/iPad/laptop (browser of PWA)
        │  HTTPS via Tailscale (alleen eigen apparaten)
        ▼
Mac Mini: dashboard-server (Node.js + TypeScript)
 ├─ Webserver: Fastify — statische UI + REST + WebSocket (streaming)
 ├─ Agent-laag: Claude Agent SDK (@anthropic-ai/claude-agent-sdk)
 │    ├─ sessie per rol (pa / coo / boek), hervat na herstart
 │    └─ canUseTool-callback → goedkeurkaarten in de UI
 ├─ rollen.json — zelfde rolconfig als de iMessage-brug (map, permissies)
 └─ launchd (KeepAlive) — zelfde vangnetpatroon als de bruggen
```

- **Toegang**: server bindt uitsluitend aan het Tailscale-adres
  (of via `tailscale serve` met automatische HTTPS). Daarbovenop één
  gedeeld toegangstoken als tweede slot. Geen poorten open naar internet.
- **Frontend**: één pagina, licht gehouden (geen zwaar framework in v1):
  rollenkolommen, chatpaneel met streaming, goedkeurkaarten,
  statusbalk. Installeerbaar als PWA (icoon op je homescherm).
- **Waarom de Agent SDK i.p.v. `claude -p`**: streaming per token,
  nette permissie-callbacks (de goedkeurknoppen), en sessies die de
  server zelf beheert in plaats van los gespawnde processen.

## Gefaseerd bouwen

**v0 — het skelet (eerste bouwklus)**
- Eén rol (PA), chatten met streaming antwoord, sessie overleeft
  serverherstart, Tailscale-only + token, launchd-installatie.
- Statusbalk: draaien de bruggen? (launchctl-check Prometheus, iMessage-brug,
  claude-rc) — daarmee is het dashboard meteen je storingsmonitor.

**v1 — het rollenmodel**
- Alle drie rollen naast elkaar, per rol sessiebeheer (nieuw/hervat).
- Goedkeurkaarten via canUseTool: per rol instelbaar welke acties vrij
  zijn en welke een klik vragen (COO strikt, boek ruim).
- Rapportviewer: bestanden uit de werkmappen (uitvoer, manuscripten) lezen.

**v2 — comfort**
- Pushnotificaties (web push) bij goedkeurvragen en afgeronde taken.
- Geplande routines zichtbaar en aan/uit te zetten.
- Bestanden uploaden (foto van een stuk → naar inbox van een rol).

## Openstaande keuzes (voor Christiaan)

1. **Goedkeurgranulariteit COO**: alles laten goedkeuren behalve
   lezen+rapport schrijven (streng), of het profiel uit de iMessage-brug
   volgen (acceptEdits)? Voorstel: streng starten, versoepelen op ervaring.
2. **v0-scope**: statusmonitor van de bruggen in v0 meenemen (voorstel: ja,
   klein werk, direct nut) of puur chat eerst?
3. **Notificaties**: web push (werkt op iPhone sinds iOS 16.4, vereist
   PWA-installatie) of via een bestaande brug (iMessage/Telegram) sturen?

## Beheer

Zelfde patroon als de bruggen: eigen privérepo (`cpdekok/mm-dashboard`),
launchd met KeepAlive, logbestanden in de projectmap, `status`-endpoint
voor de andere bruggen om óók dit dashboard te bewaken.
