#!/usr/bin/env bash
# Toggle HyprSidebar on/off
SIDEBAR_PIDFILE="/tmp/hyprsidebar.pid"

if [ -f "$SIDEBAR_PIDFILE" ] && kill -0 "$(cat "$SIDEBAR_PIDFILE")" 2>/dev/null; then
    kill "$(cat "$SIDEBAR_PIDFILE")" 2>/dev/null
    rm -f "$SIDEBAR_PIDFILE"
else
    python3 "$HOME/.config/hypr/settings/ui/sidebar.py" &
    echo $! > "$SIDEBAR_PIDFILE"
fi
