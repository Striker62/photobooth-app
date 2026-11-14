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


@router.get("")
def status():
    try:
        service = subprocess.run(
            ("systemctl", "--user", "is-active", "photobooth-guestbook.service"),
            capture_output=True, text=True, timeout=3,
        )
        state = service.stdout.strip() or "unknown"
    except (OSError, subprocess.TimeoutExpired):
        state = "unknown"
    recordings = []
    if RECORDINGS.is_dir():
        for path in sorted(RECORDINGS.iterdir(), reverse=True):
            if RECORDING_NAME.fullmatch(path.name) and path.is_file() and not path.is_symlink():
                recordings.append(path.name)
    return {"state": state, "recordings": recordings}


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
