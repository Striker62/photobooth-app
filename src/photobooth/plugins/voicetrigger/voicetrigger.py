import json
import logging
import selectors
import subprocess
import threading
import time
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from ... import CONFIG_PATH
from ...services.config.baseconfig import BaseConfig
from ...utils.exceptions import ProcessMachineOccupiedError
from ...utils.video_microphone import microphone, microphone_lock, voice_test_active
from .. import hookimpl
from ..base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class VoiceTriggerConfig(BaseConfig):
    model_config = SettingsConfigDict(title="Sprachauslöser", json_file=f"{CONFIG_PATH}plugin_voicetrigger.json")
    enabled: bool = False
    wake_word: str = "kamera"
    photo_word: str = "foto"
    video_word: str = "video"


class Voicetrigger(BasePlugin[VoiceTriggerConfig]):
    def __init__(self):
        super().__init__()
        self._config = VoiceTriggerConfig()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @hookimpl
    def photobooth_plugin_config(self):
        return VoiceTriggerConfig

    @hookimpl
    def photobooth_plugin_loaded(self, config):
        self._config = config

    @hookimpl
    def start(self):
        if self._config.enabled and not (self._thread and self._thread.is_alive()):
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="voice-trigger", daemon=True)
            self._thread.start()

    @hookimpl
    def stop(self):
        from ...routers.api import video_guestbook

        video_guestbook.voice_stop_listener = None
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self):
        try:
            from vosk import KaldiRecognizer, Model

            from ...container import container
            from ...routers.api import video_guestbook

            wake = " ".join(self._config.wake_word.lower().split())
            command = " ".join(self._config.photo_word.lower().split())
            if not wake or not command or wake == command:
                raise ValueError("Set distinct wake and photo phrases")
            model = Model(str(Path.home() / "VoiceTrigger" / "model"))
            video_phrase = f"{wake} {' '.join(self._config.video_word.lower().split())}"

            def stop_listener(rate):
                recognizer = KaldiRecognizer(model, rate, json.dumps([video_phrase, "[unk]"]))

                def listen(data):
                    if self._stop.is_set() or not recognizer.AcceptWaveform(data):
                        return False
                    return json.loads(recognizer.Result()).get("text") == video_phrase

                return listen

            video_guestbook.voice_stop_listener = stop_listener
            service = container.processing_service
            while not self._stop.is_set():
                device = microphone()
                if device and not voice_test_active.is_set() and not service.is_occupied() and microphone_lock.acquire(blocking=False):
                    try:
                        if not service.is_occupied():
                            recognizer = KaldiRecognizer(model, 16000, json.dumps([wake, command, f"{wake} {command}", video_phrase, "[unk]"]))
                            self._listen(device, service, recognizer, wake, command, video_phrase)
                    finally:
                        microphone_lock.release()
                self._stop.wait(0.5)
        except Exception:
            logger.exception("Sprachauslöser konnte nicht gestartet werden oder wurde beendet")

    def _listen(self, device, service, recognizer, wake, command, video_phrase):
        from fastapi import HTTPException

        from ...routers.api import video_guestbook

        args = ["arecord", "-q", "-D", device, "-t", "raw", "-f", "S16_LE", "-r", "16000", "-c", "1"]
        with subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=0) as audio, selectors.DefaultSelector() as selector:
            assert audio.stdout is not None
            selector.register(audio.stdout, selectors.EVENT_READ)
            wake_until = 0.0
            try:
                while not self._stop.is_set() and not voice_test_active.is_set() and not service.is_occupied():
                    if not selector.select(timeout=0.1):
                        continue
                    data = audio.stdout.read(4096)
                    if not data:
                        break
                    if not recognizer.AcceptWaveform(data):
                        continue
                    text = json.loads(recognizer.Result()).get("text", "")
                    if voice_test_active.is_set():
                        break
                    now = time.monotonic()
                    if text == wake:
                        wake_until = now + 4
                    if text == video_phrase:
                        try:
                            video_guestbook.toggle()
                        except HTTPException:
                            logger.info("Videogruß per Sprache derzeit nicht verfügbar")
                        break
                    if text == f"{wake} {command}" or (text == command and now <= wake_until):
                        try:
                            service.trigger_action("image", 0)
                        except ProcessMachineOccupiedError:
                            pass
                        break
            finally:
                if audio.poll() is None:
                    audio.terminate()
                    try:
                        audio.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        audio.kill()
