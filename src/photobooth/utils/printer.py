import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from urllib.parse import unquote, urlsplit


class PrinterStatus(StrEnum):
    OK = "ok"
    BUSY = "busy"
    DISABLED = "disabled"
    UNKNOWN = "unknown"

    # there are many more states but none of these can be get reliable for all printers on all platforms.
    # so we focus on the 4 most important and fallback to UNKNOWN

    # OFFLINE = "offline"
    # PAPER_OUT = "paper_out"
    # COVER_OPEN = "cover_open"
    # JAM = "jam"


@dataclass
class PrinterStateChange:
    printer: str
    old: PrinterStatus | None
    new: PrinterStatus
    raw: str


def local_lp_queue(command: str, configured_name: str) -> str | None:
    """Recognise direct CUPS submissions with an explicit destination."""
    if sys.platform != "linux":
        return None
    try:
        args = shlex.split(command)
    except ValueError:
        return None
    if not args or args[0] not in ("lp", "/usr/bin/lp") or "-d" not in args:
        return None
    index = args.index("-d") + 1
    if index >= len(args):
        return None
    name = args[index].replace("{printer_name}", configured_name)
    return name if re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", name) else None


def classify_linux(output):
    output = re.sub(r"^printer \S+ ", "", output.split("\n", 1)[0])
    if output.startswith("is idle"):
        return PrinterStatus.OK
    if output.startswith("disabled"):
        return PrinterStatus.DISABLED
    if output.startswith(("now printing", "is printing")):
        return PrinterStatus.BUSY

    return PrinterStatus.UNKNOWN


def selphy_usb_present(device_uri: str, usb_devices: Path = Path("/sys/bus/usb/devices")) -> bool | None:
    """Check the USB device belonging to the configured Gutenprint queue."""
    device = urlsplit(device_uri)
    if device.scheme != "gutenprint53+usb" or device.netloc != "canon-cp1500" or not usb_devices.is_dir():
        return None

    serial = unquote(device.path.lstrip("/"))
    if not serial:
        return None

    for entry in usb_devices.iterdir():
        try:
            vendor = (entry / "idVendor").read_text().strip()
            product = (entry / "idProduct").read_text().strip()
            if vendor == "04a9" and product == "3302" and (entry / "serial").read_text().strip() == serial:
                return True
        except FileNotFoundError:
            continue
        except OSError:
            return None
    return False


def local_print_problem(printer_name: str) -> str | None:
    """Report CUPS faults or a missing Selphy USB device."""
    status, detail = get_printer_status_linux(printer_name)
    if status == PrinterStatus.DISABLED:
        return "paused"
    if re.search(
        r"paper feed|no paper(?: tray)?|out of paper|paper (?:empty|out|jam)|"
        r"media-(?:empty|jam|needed)|marker-supply-empty|"
        r"(?:ink|ribbon|cartridge) (?:empty|out|depleted)|no (?:ink|ribbon|cartridge)|"
        r"printer open failure|failed to claim interface",
        detail,
    ):
        return "unavailable"
    try:
        device = subprocess.check_output(
            ["lpstat", "-v", printer_name],
            text=True,
            stderr=subprocess.STDOUT,
            env={**os.environ, "LC_ALL": "C"},
            timeout=2,
        ).strip()
        uri = device.removeprefix(f"device for {printer_name}: ")
        if selphy_usb_present(uri) is False:
            return "unavailable"
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


def get_printer_status_linux(printer_name: str):
    try:
        # force english because later parsing.
        status_raw = subprocess.check_output(
            ["lpstat", "-p", printer_name, "-l"],
            text=True,
            stderr=subprocess.STDOUT,
            env={**os.environ, "LANG": "C", "LC_ALL": "C"},
            timeout=2,
        ).lower()
    except Exception as exc:
        raise RuntimeError(f"Error getting stats for printer '{printer_name}'") from exc

    status = classify_linux(status_raw)

    return status, status_raw


# -------------------------
# Windows (pywin32)
# -------------------------
def classify_windows(status_flags: int):
    BUSY = 0x00000200
    PRINTER_STATUS_PAUSED = 0x00000001
    OK = 0x00000000

    if status_flags == OK:
        return PrinterStatus.OK
    if status_flags & PRINTER_STATUS_PAUSED:
        return PrinterStatus.DISABLED
    if status_flags & BUSY:
        return PrinterStatus.BUSY

    return PrinterStatus.UNKNOWN


def get_printer_status_windows(printer_name: str) -> tuple[PrinterStatus, int]:
    import pywintypes  # pyright: ignore[reportMissingModuleSource]
    import win32print  # pyright: ignore[reportMissingModuleSource]

    try:
        handle = win32print.OpenPrinter(printer_name)
    except pywintypes.error as exc:
        raise RuntimeError(f"Error opening printer '{printer_name}' to get status") from exc

    try:
        info6 = win32print.GetPrinter(handle, 6)
        status_raw = info6["Status"]
    finally:
        win32print.ClosePrinter(handle)

    status = classify_windows(status_raw)

    return status, status_raw


# -------------------------
# Unified API
# -------------------------
def get_printer_status(printer_name):
    if sys.platform == "win32":
        return get_printer_status_windows(printer_name)
    elif sys.platform in ("linux", "darwin"):
        return get_printer_status_linux(printer_name)

    raise OSError(f"System '{sys.platform}' not supported.")


# -------------------------
# State Machine + Polling
# -------------------------
def monitor_printer(printer_name, callback, interval=1.0):
    last_state: PrinterStatus | None = None

    while True:
        new_state, new_state_raw = get_printer_status(printer_name)

        if new_state != last_state:
            event = PrinterStateChange(
                printer=printer_name,
                old=last_state,
                new=new_state,
                raw=f"0x{new_state_raw:08X}",
            )
            callback(event)
            last_state = new_state

        time.sleep(interval)


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    PRINTER = "PDF"  # or "Brother_MFC_L2720DW_series" or "Canon_SELPHY_CP1300"

    def on_state_change(event: PrinterStateChange):
        print(f"[STATE CHANGE] {event.printer}: {event.old} Ã¢â€ â€™ {event.new}")
        print("RAW:", event.raw)

    monitor_printer(PRINTER, on_state_change, interval=1.0)
