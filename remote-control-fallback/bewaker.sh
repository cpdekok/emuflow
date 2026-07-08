#!/bin/bash
# Houdt de Claude Remote Control-server draaiend in een tmux-sessie.
# Wordt zelf bewaakt door launchd (KeepAlive), dus dubbel vangnet:
# crasht claude -> deze lus herstart hem; crasht dit script -> launchd herstart het.

SESSIE="claude-rc"
NAAM="Mac Mini"

TMUX="$(command -v tmux)"
CLAUDE="$(command -v claude)"
if [ -z "$TMUX" ] || [ -z "$CLAUDE" ]; then
  echo "tmux of claude niet gevonden in PATH ($PATH)" >&2
  exit 1
fi

while true; do
  if ! "$TMUX" has-session -t "$SESSIE" 2>/dev/null; then
    echo "$(date '+%F %T') remote-control-server (her)starten"
    "$TMUX" new-session -d -s "$SESSIE" -c "$HOME" \
      "$CLAUDE remote-control --name '$NAAM' --spawn same-dir"
  fi
  sleep 30
done
