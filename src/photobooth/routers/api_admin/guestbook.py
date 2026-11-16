import re
import stat
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..api.video_guestbook import ROOT as VIDEO_ROOT
from ..api.video_guestbook import VIDEOS, lock as video_lock, microphone, recording_seconds, video_key
from pydantic import BaseModel, Field

router = APIRouter(prefix="/guestbook", tags=["guestbook"])
ROOT = Path.home() / "AudioGuestbook"
GREETING = ROOT / "greeting.wav"
RECORDINGS = ROOT / "recordings"
TIMESTAMP_NAME = r"PB[0-9]{4}(?:-[0-9]{2}){5}(?:-[0-9]{6})?"
RECORDING_NAME = re.compile(rf"(?:{TIMESTAMP_NAME}|[0-9]{{8}}-[0-9]{{6}}-[0-9]{{6}}|gaestebuch_eintrag[0-9]+)\.wav")
VIDEO_NAME = re.compile(rf"(?:{TIMESTAMP_NAME}|[0-9a-f]{{32}})\.mp4")
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
    return {
        "state": state,
        "enabled": unit_state == "enabled",
        "installed": unit_state in ("enabled", "disabled"),
        "has_greeting": GREETING.is_file() and not GREETING.is_symlink(),
        "recordings": audio_recordings(),
    }


def audio_recordings() -> list[str]:
    if not RECORDINGS.is_dir():
        return []
    return [
        path.name
        for path in sorted(RECORDINGS.iterdir(), reverse=True)
        if RECORDING_NAME.fullmatch(path.name) and not path.is_symlink() and path.is_file()
    ]


@router.get("/greeting")
def greeting():
    if not GREETING.is_file() or GREETING.is_symlink():
        raise HTTPException(404, "Keine Ansage hinterlegt.")
    return FileResponse(GREETING, media_type="audio/wav", headers={"Cache-Control": "no-store"})


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


@router.get("/videos")
def videos():
    if not VIDEOS.is_dir():
        return []
    return [
        {"name": path.name, "created": path.stat().st_mtime}
        for path in VIDEOS.glob("*.mp4")
        if VIDEO_NAME.fullmatch(path.name) and not path.is_symlink() and path.is_file()
    ]


@router.get("/video-settings")
def video_settings():
    return {
        "enabled": not (VIDEO_ROOT / "disabled").exists(),
        "configured": bool(microphone()),
        "show_button": not (VIDEO_ROOT / "hide-button").exists(),
        "seconds": recording_seconds(),
        "key": video_key(),
        "gpio": gpio_pin(),
    }


def gpio_pin():
    try:
        return (VIDEO_ROOT / "gpio").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


class VideoControls(BaseModel):
    key: str = Field(pattern=r"^[a-z0-9]?$")
    gpio: str = Field(pattern=r"^(?:[2-9]|1[0-9]|2[0-7])?$")
    show_button: bool
    seconds: int = Field(ge=1, le=300)


@router.put("/video-settings")
def set_video_controls(controls: VideoControls):
    with video_lock:
        VIDEO_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = VIDEO_ROOT / "duration.tmp"
        temporary.write_text(str(controls.seconds), encoding="utf-8")
        temporary.replace(VIDEO_ROOT / "duration")
        for name, value in (("key", controls.key), ("gpio", controls.gpio)):
            temporary = VIDEO_ROOT / f"{name}.tmp"
            temporary.write_text(value, encoding="utf-8")
            temporary.replace(VIDEO_ROOT / name)
        marker = VIDEO_ROOT / "hide-button"
        if controls.show_button:
            marker.unlink(missing_ok=True)
        else:
            marker.touch()
        return video_settings()


@router.put("/video-settings/{enabled}")
def set_video_enabled(enabled: bool):
    VIDEO_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = VIDEO_ROOT / "disabled"
    if enabled:
        marker.unlink(missing_ok=True)
    else:
        marker.touch()
    return video_settings()


def video_path(name: str):
    path = VIDEOS / name
    if not VIDEO_NAME.fullmatch(name) or path.is_symlink() or not path.is_file():
        raise HTTPException(404)
    return path


@router.get("/videos/{name}")
def video(name: str):
    return FileResponse(video_path(name), media_type="video/mp4", headers={"Cache-Control": "no-store"})


@router.delete("/videos/{name}", status_code=204)
def delete_video(name: str):
    video_path(name).unlink(missing_ok=True)


@router.delete("/all-media", status_code=204)
def delete_all_media():
    from ..api.mediacollection import api_gallery_delete_all

    api_gallery_delete_all()
    failed = 0
    for directory, pattern in ((RECORDINGS, RECORDING_NAME), (VIDEOS, VIDEO_NAME)):
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if pattern.fullmatch(path.name) and path.is_file() and not path.is_symlink():
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    failed += 1
    if failed:
        raise HTTPException(500, f"{failed} Gästebuchdateien konnten nicht gelöscht werden.")
