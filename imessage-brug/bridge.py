#!/usr/bin/env python3
"""iMessage-brug naar Claude Code op de Mac Mini.

Leest binnenkomende iMessages uit de Berichten-database (chat.db), stuurt ze
als opdracht naar Claude Code (headless, met sessiegeheugen per rol) en
beantwoordt via AppleScript.

Routering per bericht:
    "coo: maak het weekrapport"   -> rol "coo"
    "boek: schrijf hoofdstuk 1"   -> rol "boek"
    "pa: herinner me aan ..."     -> rol "pa"
    zonder prefix                 -> standaard_rol uit config.json

Commando's:
    status          -> toont rollen, sessies en uptime
    nieuw           -> nieuwe sessie voor de standaardrol
    coo: nieuw      -> nieuwe sessie voor die rol
    ping            -> pong (om de brug te testen)

Vereisten op de MM: ingelogd in Berichten, Full Disk Access voor de
Python-interpreter die dit script draait, Claude Code CLI in PATH.
"""

import json
import re
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
CONFIG = json.loads((HIER / "config.json").read_text())
STATE_PAD = HIER / "state.json"
LOG_PAD = HIER / "brug.log"
CHAT_DB = Path.home() / "Library" / "Messages" / "chat.db"
START = time.time()


def log(msg: str) -> None:
    regel = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
    print(regel, flush=True)
    with LOG_PAD.open("a") as f:
        f.write(regel + "\n")


def laad_state() -> dict:
    if STATE_PAD.exists():
        return json.loads(STATE_PAD.read_text())
    return {"laatste_rowid": None, "sessies": {}}


def bewaar_state(state: dict) -> None:
    STATE_PAD.write_text(json.dumps(state, indent=2))


def tekst_uit_attributed_body(blob: bytes) -> str:
    """Nieuwere macOS-versies bewaren de tekst in attributedBody i.p.v. text.

    Pragmatische extractie uit de typedstream: de berichttekst volgt op de
    NSString/NSMutableString-marker als lengte-geprefixte UTF-8.
    """
    if not blob:
        return ""
    m = re.search(rb"NSString\x01\x94\x84\x01\+", blob) or re.search(
        rb"NSMutableString\x01\x94\x84\x01\+", blob
    )
    if not m:
        return ""
    rest = blob[m.end():]
    if not rest:
        return ""
    lengte = rest[0]
    start = 1
    if lengte == 0x81:  # lengte > 127: twee bytes little-endian
        lengte = int.from_bytes(rest[1:3], "little")
        start = 3
    try:
        return rest[start:start + lengte].decode("utf-8", errors="replace")
    except Exception:
        return ""


def nieuwe_berichten(state: dict) -> list[tuple[int, str, str]]:
    """Geeft [(rowid, afzender, tekst)] voor nieuwe inkomende berichten."""
    con = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        if state["laatste_rowid"] is None:
            cur.execute("SELECT COALESCE(MAX(ROWID), 0) FROM message")
            state["laatste_rowid"] = cur.fetchone()[0]
            bewaar_state(state)
            return []
        cur.execute(
            """
            SELECT m.ROWID, h.id, m.text, m.attributedBody
            FROM message m JOIN handle h ON m.handle_id = h.ROWID
            WHERE m.ROWID > ? AND m.is_from_me = 0
            ORDER BY m.ROWID
            """,
            (state["laatste_rowid"],),
        )
        resultaat = []
        for rowid, afzender, tekst, blob in cur.fetchall():
            state["laatste_rowid"] = rowid
            inhoud = (tekst or "").strip() or tekst_uit_attributed_body(blob).strip()
            if inhoud:
                resultaat.append((rowid, afzender, inhoud))
        bewaar_state(state)
        return resultaat
    finally:
        con.close()


def stuur_imessage(naar: str, tekst: str) -> None:
    maxlen = CONFIG.get("max_antwoord_lengte", 3500)
    delen = [tekst[i:i + maxlen] for i in range(0, len(tekst), maxlen)] or [""]
    for deel in delen:
        script = (
            'tell application "Messages"\n'
            '  set svc to 1st account whose service type = iMessage\n'
            f'  send {json.dumps(deel)} to participant {json.dumps(naar)} of svc\n'
            "end tell"
        )
        subprocess.run(["osascript", "-e", script], check=False, timeout=30)


def kies_rol(tekst: str) -> tuple[str, str]:
    m = re.match(r"^(\w+)\s*:\s*(.+)$", tekst, re.DOTALL)
    if m and m.group(1).lower() in CONFIG["rollen"]:
        return m.group(1).lower(), m.group(2).strip()
    return CONFIG["standaard_rol"], tekst


def vraag_claude(rol: str, prompt: str, state: dict) -> str:
    werkmap = Path(CONFIG["rollen"][rol]["map"]).expanduser()
    if not werkmap.is_dir():
        return f"⚠️ Werkmap voor rol '{rol}' bestaat niet: {werkmap}"
    cmd = [CONFIG.get("claude_pad", "claude"), "-p", prompt, "--output-format", "json"]
    cmd += CONFIG["rollen"][rol].get("claude_argumenten", [])
    sessie = state["sessies"].get(rol)
    if sessie:
        cmd += ["--resume", sessie]
    log(f"[{rol}] claude start ({'vervolg' if sessie else 'nieuwe sessie'})")
    try:
        uit = subprocess.run(
            cmd, cwd=werkmap, capture_output=True, text=True,
            timeout=CONFIG.get("claude_timeout", 1800),
        )
    except subprocess.TimeoutExpired:
        return "⚠️ Claude reageerde niet binnen de tijdslimiet; probeer het opnieuw of stuur 'nieuw'."
    if uit.returncode != 0:
        log(f"[{rol}] fout: {uit.stderr[:500]}")
        # Sessie kan verlopen zijn; één keer opnieuw zonder --resume
        if sessie:
            state["sessies"].pop(rol, None)
            bewaar_state(state)
            return vraag_claude(rol, prompt, state)
        return f"⚠️ Claude gaf een fout: {uit.stderr[:300] or 'onbekend'}"
    try:
        data = json.loads(uit.stdout)
        state["sessies"][rol] = data.get("session_id", state["sessies"].get(rol))
        bewaar_state(state)
        return data.get("result") or "(leeg antwoord)"
    except json.JSONDecodeError:
        return uit.stdout.strip()[:4000] or "(geen uitvoer)"


def verwerk(afzender: str, tekst: str, state: dict) -> str:
    kaal = tekst.strip().lower()
    if kaal == "ping":
        return "pong 🏓 — brug draait"
    if kaal == "status":
        uptime = int(time.time() - START)
        regels = [f"Brug actief ({uptime // 3600}u{(uptime % 3600) // 60:02d}m). Rollen:"]
        for rol, info in CONFIG["rollen"].items():
            sessie = "sessie actief" if state["sessies"].get(rol) else "geen sessie"
            regels.append(f"• {rol} → {info['map']} ({sessie})")
        regels.append(f"Standaardrol: {CONFIG['standaard_rol']}")
        return "\n".join(regels)
    rol, inhoud = kies_rol(tekst)
    if inhoud.strip().lower() in ("nieuw", "reset"):
        state["sessies"].pop(rol, None)
        bewaar_state(state)
        return f"Nieuwe sessie voor rol '{rol}'."
    return vraag_claude(rol, inhoud, state)


def main() -> None:
    if not CHAT_DB.exists():
        raise SystemExit(f"chat.db niet gevonden op {CHAT_DB} — is Berichten ingericht?")
    toegestaan = set(CONFIG["toegestane_afzenders"])
    state = laad_state()
    log(f"Brug gestart. Toegestane afzenders: {', '.join(toegestaan)}")
    while True:
        try:
            for _rowid, afzender, tekst in nieuwe_berichten(state):
                if afzender not in toegestaan:
                    log(f"Genegeerd bericht van onbekende afzender {afzender}")
                    continue
                log(f"[{afzender}] > {tekst[:120]}")
                if len(tekst) > 40 or ":" in tekst:
                    stuur_imessage(afzender, "⏳ Bezig…")
                antwoord = verwerk(afzender, tekst, state)
                stuur_imessage(afzender, antwoord)
                log(f"[{afzender}] < {antwoord[:120]}")
        except Exception as e:  # blijf draaien; launchd herstart bij crash
            log(f"FOUT in hoofdlus: {e!r}")
        time.sleep(CONFIG.get("poll_interval", 3))


if __name__ == "__main__":
    main()
