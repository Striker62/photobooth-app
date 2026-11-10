#!/usr/bin/env python3
"""Configure the tested USB printer profile; default operation is read-only."""

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout


def discover_usb(output):
    return sorted({
        line.split()[1] for line in output.splitlines()
        if len(line.split()) >= 2
        and line.split()[0] == "direct"
        and line.split()[1].startswith("gutenprint53+usb://canon-cp1500/")
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write the profile to CUPS")
    parser.add_argument("--uri", help="Select one of the discovered CP1500 USB addresses")
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("Run this script on the Raspberry Pi (Linux).")
    if os.geteuid() != 0:
        parser.error("Run with sudo so CUPS can discover the USB backend.")
    for command in ("lpinfo", "lpadmin", "lpstat"):
        if not shutil.which(command):
            parser.error(f"Missing {command}; install cups and cups-client first.")

    profile = json.loads(Path(__file__).with_name("cp1500.json").read_text())
    models = run("lpinfo", "-m")
    model_lines = [line for line in models.splitlines() if line.split() and line.split()[0] == profile["model"]]
    if not model_lines:
        parser.error("CP1500 Gutenprint driver missing. Follow README.md to install Gutenprint 5.3.5.")
    devices = discover_usb(run("lpinfo", "-v"))
    if not devices:
        parser.error("No Gutenprint CP1500 USB device found. Check power, USB cable and driver installation.")
    uri = args.uri
    if uri is None and len(devices) == 1:
        uri = devices[0]
    if uri not in devices:
        parser.error("Select one discovered address using --uri: " + ", ".join(devices))

    # Do not repoint an unrelated queue or automatically resume an existing one.
    env = dict(os.environ, LC_ALL="C")
    queues = subprocess.run(["lpstat", "-v"], check=True, text=True, capture_output=True, env=env).stdout
    prefix = f"device for {profile['queue']}: "
    existing = next((line[len(prefix):].strip() for line in queues.splitlines() if line.startswith(prefix)), None)
    if existing is not None and existing != uri:
        parser.error("Queue already points to a different device; no settings changed.")
    command = ["lpadmin", "-p", profile["queue"]]
    if existing is None:
        command.append("-E")
    command.extend(["-v", uri, "-m", profile["model"]])
    for key, value in profile["options"].items():
        command.extend(["-o", f"{key}={value}"])
    print(model_lines[0])
    print("Planned command:", shlex.join(command))
    if not args.apply:
        print("Preview only. Re-run with --apply to configure this queue.")
        return
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    print(run("lpstat", "-p", profile["queue"], "-l"))
    print("Photobooth printer_name:", profile["queue"])
    print("Photobooth share_command:", profile["photobooth_command"])
    print("No print job was submitted. Existing paused queues were not resumed.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {shlex.join(exc.cmd)}\n{exc.stderr or ''}", file=sys.stderr)
        sys.exit(1)
