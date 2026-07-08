# Claude Remote Control als fallback-brug (Mac Mini)

De officiële afstandsbediening van Claude Code: de server draait op de MM,
jij stuurt sessies aan via de **Claude-app op je telefoon** (tabblad Code)
of **claude.ai/code** in een browser. Geen eigen infrastructuur — als
Telegram/Hermes of de iMessage-brug plat ligt, werkt deze route nog.

## Vereisten

- Claude Code v2.1.51+ op de MM, ingelogd met je claude.ai-account
  (`/login`; Pro/Max-abonnement — API-keys werken niet).
- Standaard Anthropic-endpoint (api.anthropic.com). **Let op:** draait een
  rol later via AWS Bedrock/Vertex (EU-route voor kantoordata), dan werkt
  Remote Control dáár niet — deze fallback is voor besturing, niet voor de
  trap 2-kantoorprocessen.
- `tmux` (`brew install tmux`).

## Installatie

```bash
cd ~/remote-control-fallback
chmod +x bewaker.sh
sed "s|__MAP__|$(pwd)|g" com.cpdekok.claude-rc.plist \
  > ~/Library/LaunchAgents/com.cpdekok.claude-rc.plist
launchctl load ~/Library/LaunchAgents/com.cpdekok.claude-rc.plist
```

De bewaker start een tmux-sessie `claude-rc` met
`claude remote-control --name "Mac Mini" --spawn same-dir`:

- **launchd** herstart de bewaker als die crasht (KeepAlive);
- **de bewaker** herstart de server als die stopt (check elke 30 s);
- terminal sluiten maakt niets uit — alles draait in tmux.

## Gebruik vanaf je telefoon

1. Open de Claude-app → tabblad **Code**.
2. Zoek de sessie **"Mac Mini"** (groene stip = online) en tik erop.
3. Je kunt nu opdrachten geven alsof je achter de MM zit. Nieuwe sessies
   starten in je home-map; zeg gewoon "ga naar ~/herschool" of
   "werk in ~/kantoor-agents/coo" om een rol te laden.

Lokaal meekijken op de MM: `tmux attach -t claude-rc` (loskoppelen met
Ctrl-B, D). Daar staat ook de sessie-URL/QR-code.

## Beheer

```bash
launchctl list | grep claude-rc        # draait de bewaker?
tmux has-session -t claude-rc && echo "server draait"
tail -f ~/remote-control-fallback/bewaker.log
launchctl unload ~/Library/LaunchAgents/com.cpdekok.claude-rc.plist  # alles stoppen
tmux kill-session -t claude-rc
```

## Bekende beperkingen (uit de documentatie)

- Netwerkstoring langer dan ±10 min beëindigt de sessie — de bewaker
  start dan automatisch een verse server; open die opnieuw in de app.
- Interactieve terminalcommando's (zoals `/resume` met kiezer) werken
  niet vanaf de telefoon.
- Docs: https://code.claude.com/docs/en/remote-control
