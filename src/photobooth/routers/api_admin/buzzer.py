import os
import re
import subprocess
import sys

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/buzzer", tags=["buzzer"])
BUZZER_NAME = "photobooth-app buzzer"


def bluetooth(*args: str, timeout: int = 5) -> subprocess.CompletedProcess[str]:
    if sys.platform != "linux":
        raise HTTPException(501, "Bluetooth-Verwaltung ist unter Linux verfügbar.")
    try:
        return subprocess.run(
            ("bluetoothctl", *args),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(503, "Bluetooth ist nicht erreichbar oder antwortet zu langsam.") from exc


@router.get("")
def status():
    controller = bluetooth("show")
    if controller.returncode or not re.search(r"^\s*Powered: yes\s*$", controller.stdout, re.MULTILINE):
        return {"state": "unavailable"}

    devices = bluetooth("devices", "Paired")
    if devices.returncode:
        raise HTTPException(503, "Gekoppelte Bluetooth-Geräte konnten nicht abgefragt werden.")

    pattern = rf"Device ((?:[0-9A-Fa-f]{{2}}:){{5}}[0-9A-Fa-f]{{2}}) {re.escape(BUZZER_NAME)}"
    addresses = [match[1] for line in devices.stdout.splitlines() if (match := re.fullmatch(pattern, line))]
    if not addresses:
        return {"state": "unpaired"}
    if len(addresses) > 1:
        return {"state": "multiple"}

    address = addresses[0]
    device = bluetooth("info", address)
    connected = re.search(r"^\s*Connected: (yes|no)\s*$", device.stdout, re.MULTILINE)
    if device.returncode or connected is None:
        raise HTTPException(503, "Der Verbindungsstatus des Buzzers konnte nicht abgefragt werden.")
    return {"state": "connected" if connected[1] == "yes" else "disconnected", "address": address}


@router.post("/connect")
def connect():
    current = status()
    if current["state"] == "connected":
        return current
    if current["state"] != "disconnected":
        raise HTTPException(409, "Zum Verbinden muss Bluetooth aktiv und genau ein Buzzer gekoppelt sein.")

    bluetooth("--timeout", "12", "connect", current["address"], timeout=15)
    current = status()
    if current["state"] != "connected":
        raise HTTPException(503, "Verbindung fehlgeschlagen. Prüfe, ob der Buzzer eingeschaltet und verfügbar ist.")
    return current
