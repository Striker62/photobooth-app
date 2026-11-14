import re
import stat
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/guestbook", tags=["guestbook"])
ROOT = Path.home() / "AudioGuestbook"
RECORDINGS = ROOT / "recordings"
RECORDING_NAME = re.compile(r"(?:[0-9]{8}-[0-9]{6}-[0-9]{6}|gaestebuch_eintrag[0-9]+)\.wav")
UNIT = "photobooth-guestbook.service"


def systemctl(*args: str, timeout: int = 3) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("systemctl", "--user", *args, UNIT),
        capture_output=True, text=True, timeout=timeout,
    )


@router.get("")
def status():
    try:
        service = systemctl("is-active")
        state = service.stdout.strip() or "unknown"
        unit_state = systemctl("is-enabled").stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        state = "unknown"
        unit_state = ""
    recordings = []
    if RECORDINGS.is_dir():
        for path in sorted(RECORDINGS.iterdir(), reverse=True):
            if RECORDING_NAME.fullmatch(path.name) and path.is_file() and not path.is_symlink():
                recordings.append(path.name)
    return {"state": state, "enabled": unit_state == "enabled", "installed": unit_state in ("enabled", "disabled"), "recordings": recordings}


@router.post("/service/{action}")
def control(action: str):
    if action not in ("enable", "disable"):
        raise HTTPException(404)
    try:
        result = systemctl(action, "--now", timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(503, "Der Telefondienst ist nicht erreichbar oder antwortet zu langsam.") from exc
    if result.returncode:
        raise HTTPException(503, result.stderr.strip() or "Der Telefondienst konnte nicht umgeschaltet werden.")
    return status()


def recording(name: str) -> Path:
    path = RECORDINGS / name
    if not RECORDING_NAME.fullmatch(name):
        raise HTTPException(404)
    try:
        if stat.S_ISREG(path.lstat().st_mode):
            return path
    except FileNotFoundError:
        pass
    raise HTTPException(404, "Aufnahme nicht gefunden.")


@router.get("/recordings/{name}")
def audio(name: str):
    return FileResponse(recording(name), media_type="audio/wav", headers={"Cache-Control": "no-store"})


@router.delete("/recordings/{name}", status_code=204)
def delete(name: str):
    recording(name).unlink(missing_ok=True)
