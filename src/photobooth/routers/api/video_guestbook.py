import logging
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...container import container
from ...utils.exceptions import ProcessMachineOccupiedError

router = APIRouter(prefix="/video-guestbook", tags=["video-guestbook"])
ROOT = Path.home() / "VideoGuestbook"
PENDING = ROOT / "pending"
VIDEOS = ROOT / "recordings"
RECORD_SECONDS = 15
logger = logging.getLogger(__name__)
draft_lock = threading.Lock()


def microphone() -> str:
    if sys.platform != "linux":
        return ""
    try:
        return (ROOT / "microphone").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


@router.get("")
def settings():
    return {"enabled": bool(microphone()), "seconds": RECORD_SECONDS}


@router.post("/record")
def record():
    device = microphone()
    if not device:
        raise HTTPException(404, "Videogästebuch ist deaktiviert.")
    token = uuid4().hex
    video = None
    audio = PENDING / f"{token}.wav"
    output = PENDING / f"{token}.mp4"
    try:
        with container.processing_service.reserve_capture() as acquisition:
            with draft_lock:
                PENDING.mkdir(parents=True, exist_ok=True, mode=0o700)
                for path in PENDING.iterdir():
                    if time.time() - path.stat().st_mtime > 1800:
                        path.unlink(missing_ok=True)
            video = acquisition.start_recording()
            try:
                subprocess.run(
                    ["arecord", "-q", "-D", device, "-f", "S16_LE", "-r", "48000", "-c", "1",
                     "-d", str(RECORD_SECONDS), str(audio)],
                    stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=RECORD_SECONDS + 5,
                )
            finally:
                acquisition.stop_recording()
        subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(video), "-i", str(audio),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
             "-shortest", "-movflags", "+faststart", str(output)],
            capture_output=True, check=True, timeout=30,
        )
        os.chmod(output, 0o600)
    except ProcessMachineOccupiedError as exc:
        raise HTTPException(409, "Die Kamera ist gerade belegt.") from exc
    except Exception as exc:
        output.unlink(missing_ok=True)
        logger.exception("Video guestbook recording failed")
        raise HTTPException(503, "Videogruß konnte nicht aufgenommen werden. Kamera und Mikrofon prüfen.") from exc
    finally:
        audio.unlink(missing_ok=True)
        if video is not None:
            video.unlink(missing_ok=True)
    return {"token": token}


def draft(token: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", token):
        raise HTTPException(404)
    path = PENDING / f"{token}.mp4"
    if not path.is_file() or time.time() - path.stat().st_mtime > 1800:
        raise HTTPException(404, "Videovorschau ist abgelaufen.")
    return path


@router.get("/draft/{token}")
def preview(token: str):
    return FileResponse(draft(token), media_type="video/mp4", headers={"Cache-Control": "no-store"})


@router.post("/draft/{token}", status_code=204)
def save(token: str):
    with draft_lock:
        path = draft(token)
        VIDEOS.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.rename(VIDEOS / path.name)


@router.delete("/draft/{token}", status_code=204)
def discard(token: str):
    with draft_lock:
        draft(token).unlink()
