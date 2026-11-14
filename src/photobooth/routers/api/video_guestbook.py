import logging
import os
import selectors
import subprocess
import threading
import time
import wave
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ...container import container
from ...utils.exceptions import ProcessMachineOccupiedError
from ...utils.video_microphone import ROOT, microphone, microphone_lock

router = APIRouter(prefix="/video-guestbook", tags=["video-guestbook"])
VIDEOS = ROOT / "recordings"
RECORD_SECONDS = 15
COUNTDOWN_SECONDS = 3
logger = logging.getLogger(__name__)
lock = threading.Lock()
stop = threading.Event()
state = "idle"
deadline = 0.0
voice_stop_listener = None


def recording_seconds() -> int:
    try:
        seconds = int((ROOT / "duration").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return RECORD_SECONDS
    return min(300, max(1, seconds))


@router.get("")
def settings():
    with lock:
        return {
            "enabled": bool(microphone()) and not (ROOT / "disabled").exists(),
            "show_button": not (ROOT / "hide-button").exists(),
            "state": state,
            "remaining": max(0, deadline - time.monotonic()),
        }


@router.post("/toggle")
def toggle():
    global state, deadline
    with lock:
        if state == "recording":
            stop.set()
            state = "saving"
            return
        if state != "idle":
            return
        device = microphone()
        if not device or (ROOT / "disabled").exists():
            raise HTTPException(409, "Videogästebuch ist deaktiviert.")
        reservation = container.processing_service.reserve_capture()
        try:
            acquisition = reservation.__enter__()
        except ProcessMachineOccupiedError as exc:
            raise HTTPException(409, "Die Kamera ist gerade belegt.") from exc
        stop.clear()
        state = "countdown"
        deadline = time.monotonic() + COUNTDOWN_SECONDS
        try:
            threading.Thread(target=record, args=(device, acquisition, reservation, recording_seconds()), daemon=True).start()
        except RuntimeError:
            reservation.__exit__(None, None, None)
            state = "idle"
            raise


def record(device, acquisition, reservation, seconds):
    global state, deadline
    token = uuid4().hex
    audio = ROOT / f".{token}.wav"
    output = ROOT / f".{token}.mp4"
    video = None
    outcome = "saved"
    try:
        time.sleep(max(0, deadline - time.monotonic()))
        VIDEOS.mkdir(parents=True, exist_ok=True, mode=0o700)
        with microphone_lock:
            started = datetime.now()
            video = acquisition.start_recording(photo_lighting=True)
            try:
                with subprocess.Popen(
                    ["arecord", "-q", "-D", device, "-t", "raw", "-f", "S16_LE", "-r", "48000", "-c", "1"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, bufsize=0,
                ) as recorder, selectors.DefaultSelector() as selector, wave.open(str(audio), "wb") as wav:
                    assert recorder.stdout is not None
                    selector.register(recorder.stdout, selectors.EVENT_READ)
                    wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
                    listen = voice_stop_listener(48000) if voice_stop_listener else None
                    with lock:
                        state = "recording"
                        deadline = time.monotonic() + seconds
                    try:
                        while recorder.poll() is None and time.monotonic() < deadline and not stop.is_set():
                            if selector.select(timeout=0.05):
                                data = recorder.stdout.read(8192)
                                if not data:
                                    break
                                wav.writeframesraw(data)
                                if listen and listen(data):
                                    stop.set()
                        if recorder.poll() is not None:
                            raise RuntimeError("Audio recorder exited early")
                    finally:
                        if recorder.poll() is None:
                            recorder.terminate()
                            try:
                                recorder.wait(timeout=3)
                            except subprocess.TimeoutExpired:
                                recorder.kill()
                                raise
            finally:
                acquisition.stop_recording()
        with lock:
            state = "saving"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(video), "-i", str(audio),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
             "-shortest", "-movflags", "+faststart", str(output)],
            check=True, timeout=30,
        )
        os.chmod(output, 0o600)
        stem = started.strftime("PB%Y-%m-%d-%H-%M-%S")
        try:
            (VIDEOS / f"{stem}.mp4").hardlink_to(output)
        except FileExistsError:
            (VIDEOS / f"{stem}-{started:%f}.mp4").hardlink_to(output)
    except Exception:
        outcome = "error"
        logger.exception("Video guestbook recording failed")
    finally:
        try:
            audio.unlink(missing_ok=True)
            output.unlink(missing_ok=True)
            if video is not None:
                video.unlink(missing_ok=True)
        finally:
            reservation.__exit__(None, None, None)
            with lock:
                state = outcome
                deadline = time.monotonic() + 3
            time.sleep(3)
            with lock:
                state = "idle"
