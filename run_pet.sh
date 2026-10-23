#!/usr/bin/env bash
cd "$(dirname "$0")"

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# On Linux, enforce XWayland (xcb) so the pet floats, stays on top, and tracks cursor properly
if [ "$(uname)" = "Linux" ]; then
    export QT_QPA_PLATFORM="xcb;wayland"
fi

python3 main.py "$@"
