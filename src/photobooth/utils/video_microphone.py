import sys
from pathlib import Path
from threading import Event, Lock

ROOT = Path.home() / "VideoGuestbook"
microphone_lock = Lock()
voice_test_active = Event()


def microphone() -> str:
    if sys.platform != "linux":
        return ""
    try:
        return (ROOT / "microphone").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
