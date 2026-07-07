# iMessage-brug naar Claude Code (Mac Mini)

Stuur een iMessage naar de Mac Mini en krijg antwoord van Claude Code — met
sessiegeheugen per rol (PA, COO, boek) en automatische herstart via launchd
als de brug vastloopt.

```
jij (iPhone, Berichten)  ──iMessage──▶  MM: bridge.py  ──▶  claude -p (per rol)
                         ◀──iMessage──                 ◀──  antwoord
```

## Gebruik

| Bericht | Effect |
|---------|--------|
| `wat staat er vandaag op de agenda?` | gaat naar de standaardrol (pa) |
| `coo: draai de termijnbewaking` | gaat naar de COO-werkmap |
| `boek: schrijf hoofdstuk 1 van boek 1` | gaat naar het Herschool-project |
| `nieuw` / `coo: nieuw` | nieuwe sessie voor die rol |
| `status` | rollen, sessies en uptime |
| `ping` | `pong` — test of de brug draait |

## Installatie (eenmalig, op de MM)

1. **Apple ID**: gebruik bij voorkeur een **apart Apple ID** voor Berichten op
   de MM (bijv. mm-brug@icloud.com) en stuur dáárnaar. Berichten naar je
   eigen Apple ID synchroniseren onvoorspelbaar tussen je apparaten.
2. **Config**: `cp config.example.json config.json` en vul in:
   - `toegestane_afzenders`: jouw telefoonnummer en/of Apple ID —
     de brug negeert iedereen die hier niet in staat;
   - de werkmappen per rol (moeten bestaan).
3. **Full Disk Access**: Systeeminstellingen → Privacy en beveiliging →
   Volledige schijftoegang → voeg `/usr/bin/python3` toe (nodig om
   `~/Library/Messages/chat.db` te lezen).
4. **Automatisering**: bij de eerste verzending vraagt macOS toestemming om
   Berichten aan te sturen — sta toe.
5. **launchd** (auto-start + auto-herstart):
   ```bash
   sed "s|__BRUGMAP__|$(pwd)|g" com.cpdekok.imessage-brug.plist \
     > ~/Library/LaunchAgents/com.cpdekok.imessage-brug.plist
   launchctl load ~/Library/LaunchAgents/com.cpdekok.imessage-brug.plist
   ```
6. **Test**: stuur `ping` — antwoord `pong` betekent dat alles staat.

## Beheer

```bash
launchctl list | grep imessage-brug          # draait hij?
tail -f brug.log                             # live meekijken
launchctl kickstart -k gui/$(id -u)/com.cpdekok.imessage-brug   # handmatig herstarten
launchctl unload ~/Library/LaunchAgents/com.cpdekok.imessage-brug.plist  # stoppen
```

Loopt Claude zelf vast in een opdracht, stuur dan `nieuw` (of
`coo: nieuw`) — dat start een verse sessie zonder de brug te herstarten.

## Veiligheid en grenzen

- Alleen afzenders uit `toegestane_afzenders` worden verwerkt; al het
  andere wordt gelogd en genegeerd.
- De rollen draaien standaard met `--permission-mode acceptEdits`:
  bestandsbewerkingen in de werkmap mogen, maar riskante shell-commando's
  worden in headless modus geweigerd in plaats van uitgevoerd. Ruimer
  instellen kan per rol via `claude_argumenten` — doe dat bewust.
- **Kantoorinhoud**: iMessage is het kanaal voor opdrachten en
  statusmeldingen. Stuur er geen cliëntgegevens doorheen; de COO-rol werkt
  binnen zijn eigen datagrenzen (zie kantoor-agents).
- Bekende beperkingen: Apple biedt geen officiële API — een macOS-update
  kan het uitlezen van chat.db breken (de brug logt dat dan; `ping` blijft
  je test). Bijlagen (foto's/documenten) worden nog niet doorgegeven.
