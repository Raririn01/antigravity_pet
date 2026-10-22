"""
Helper script to send state triggers to the Antigravity Desktop Pet.
Usage:
  python notify.py work "Compiling..."
  python notify.py celebrate "Build Passed!"
  python notify.py happy
  python notify.py curious "Warning detected"
  python notify.py idle
  python notify.py sleep
"""

import sys
import json
import urllib.request

def send_state(state: str, message: str = ""):
    url = "http://127.0.0.1:21420/state"
    payload = json.dumps({"state": state, "message": message}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            print(f"Sent state '{state}' to pet -> Response: {resp.read().decode()}")
    except Exception as e:
        print(f"Failed to communicate with pet: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python notify.py <state> [message]")
        sys.exit(1)
    
    state_arg = sys.argv[1]
    msg_arg = sys.argv[2] if len(sys.argv) > 2 else ""
    send_state(state_arg, msg_arg)
