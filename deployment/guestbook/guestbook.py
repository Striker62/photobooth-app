"""Record a voice message after the caller dials 1."""
import logging
import os
import subprocess
import time
import wave
from datetime import datetime
from pathlib import Path

import sounddevice as sd
from gpiozero import DigitalInputDevice


def main():
    logging.basicConfig(level=logging.INFO)
    root = Path.home() / "AudioGuestbook"
    recordings = root / "recordings"
    recordings.mkdir(parents=True, exist_ok=True, mode=0o700)
    input_device = os.getenv("GUESTBOOK_INPUT") or None
    output_device = os.getenv("GUESTBOOK_OUTPUT", "default")
    with DigitalInputDevice(17, pull_up=True) as dial, DigitalInputDevice(18, pull_up=True) as hook:
        # The original telephone opens the hook contact when lifted.
        lifted = lambda: not hook.is_active
        while True:
            hook.wait_for_inactive()
            try:
                if hook.wait_for_active(timeout=2) or not lifted():
                    continue
                greeting = root / "greeting.wav"
                dial_started = False
                pulses = 0
                last_pulse = 0.0
                previous = dial.is_active

                def dialed_one():
                    nonlocal dial_started, pulses, last_pulse, previous
                    current = dial.is_active
                    now = time.monotonic()
                    if current and not previous and now - last_pulse >= 0.025:
                        dial_started = True
                        pulses += 1
                        last_pulse = now
                    previous = current
                    if pulses and now - last_pulse > 0.45:
                        digit = pulses
                        pulses = 0
                        return digit == 1
                    return False

                start_recording = play(greeting, output_device, lifted, dialed_one)
                repeat_at = time.monotonic() + 10
                while lifted() and not start_recording:
                    start_recording = dialed_one()
                    if not dial_started and time.monotonic() >= repeat_at:
                        start_recording = play(greeting, output_device, lifted, dialed_one)
                        repeat_at = float("inf")
                    time.sleep(0.005)
                if start_recording and lifted():
                    play(root / "beep.wav", output_device, lifted)
                    if lifted():
                        record(recordings, input_device, lifted)
            except (OSError, sd.PortAudioError):
                logging.exception("Telephone session failed")
            hook.wait_for_active()


def play(path, device, lifted, interrupt=None):
    if not lifted():
        return False
    interrupted = False
    with subprocess.Popen(["aplay", "-q", "-D", device, str(path)]) as player:
        while player.poll() is None and lifted():
            if interrupt is not None and interrupt():
                interrupted = True
                break
            time.sleep(0.005)
        if player.poll() is None:
            player.terminate()
        elif player.returncode:
            raise OSError(f"Cannot play {path}")
    return interrupted


def record(directory, device, lifted):
    name = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    temporary = directory / f"{name}.part"
    rate = int(sd.query_devices(device, "input")["default_samplerate"])
    try:
        with sd.RawInputStream(device=device, samplerate=rate, channels=1, dtype="int16") as stream:
            with wave.open(str(temporary), "wb") as audio:
                audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
                deadline = time.monotonic() + 300
                while lifted() and time.monotonic() < deadline:
                    block, overflow = stream.read(1024)
                    if overflow:
                        logging.warning("Audio input overflow")
                    audio.writeframesraw(block)
                captured = audio.getnframes()
        if captured:
            temporary.rename(directory / f"{name}.wav")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
