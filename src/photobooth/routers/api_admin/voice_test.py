import json
import logging
import subprocess
from pathlib import Path
from threading import Lock

from fastapi import APIRouter, HTTPException

from ...container import container
from ...utils.video_microphone import microphone, microphone_lock, voice_test_active

router = APIRouter(prefix="/voice-test", tags=["voice-test"])
logger = logging.getLogger(__name__)
test_lock = Lock()


@router.post("")
def test_voice(check_commands: bool = False):
    device = microphone()
    if not device:
        raise HTTPException(409, "USB-Mikrofon für das Videogästebuch einrichten.")
    try:
        from vosk import KaldiRecognizer, Model
    except ImportError as exc:
        raise HTTPException(503, "Vosk fehlt oder konnte nicht geladen werden.") from exc
    model_path = Path.home() / "VoiceTrigger" / "model"
    if not (model_path / "am").is_dir() or not (model_path / "conf").is_dir():
        raise HTTPException(503, "Das Vosk-Sprachmodell fehlt in ~/VoiceTrigger/model.")
    if not test_lock.acquire(blocking=False):
        raise HTTPException(409, "Ein Sprachtest läuft bereits.")
    voice_test_active.set()
    try:
        if container.processing_service.is_occupied() or not microphone_lock.acquire(timeout=2):
            raise HTTPException(409, "Kamera oder Mikrofon ist belegt.")
        try:
            if container.processing_service.is_occupied():
                raise HTTPException(409, "Die Kamera ist belegt.")
            sample = subprocess.run(
                ["arecord", "-q", "-D", device, "-t", "raw", "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", "5"],
                capture_output=True, check=True, timeout=8,
            ).stdout
        finally:
            microphone_lock.release()
        model = Model(str(model_path))
        if check_commands:
            config = container.config_service.get_current("photobooth.plugins.voicetrigger.voicetrigger", True)
            wake, photo, video = (" ".join(config[key].lower().split()) for key in ("wake_word", "photo_word", "video_word"))
            recognizer = KaldiRecognizer(model, 16000, json.dumps([wake, photo, f"{wake} {photo}", f"{wake} {video}", "[unk]"]))
        else:
            recognizer = KaldiRecognizer(model, 16000)
        phrases = []
        for offset in range(0, len(sample), 4096):
            if recognizer.AcceptWaveform(sample[offset:offset + 4096]):
                phrases.append(json.loads(recognizer.Result()).get("text", ""))
        phrases.append(json.loads(recognizer.FinalResult()).get("text", ""))
        action = None
        if check_commands:
            for index, phrase in enumerate(phrases):
                if phrase == f"{wake} {video}":
                    action = "Videogruß"
                    break
                if phrase == f"{wake} {photo}" or (phrase == photo and index > 0 and phrases[index - 1] == wake):
                    action = "Foto"
                    break
        return {"text": " ".join(filter(None, phrases)), "action": action}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Voice test failed")
        raise HTTPException(503, "Sprachtest fehlgeschlagen. Mikrofon und Vosk-Modell prüfen.") from exc
    finally:
        voice_test_active.clear()
        test_lock.release()
