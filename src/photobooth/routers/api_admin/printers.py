import os
import re
import subprocess
import sys

from fastapi import APIRouter, HTTPException

from ...utils.printer import classify_linux

router = APIRouter(prefix="/printers", tags=["printers"])


def cups(*args: str) -> str:
    if sys.platform != "linux":
        raise HTTPException(501, "CUPS queue management is available on Linux.")
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "LC_ALL": "C", "CUPS_SERVER": "/run/cups/cups.sock"},
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(503, "Cannot reach local CUPS or the command timed out.") from exc
    if result.returncode:
        raise HTTPException(503, result.stderr.strip() or "CUPS rejected the request.")
    return result.stdout.strip()


@router.get("")
def printers():
    return [line.split()[0] for line in cups("lpstat", "-a").splitlines() if line.strip()]


def require_queue(queue: str):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", queue) or queue not in printers():
        raise HTTPException(404, "Unknown local printer queue.")


def active_jobs(queue: str):
    jobs = []
    for line in cups("lpstat", "-W", "not-completed", "-o", queue).splitlines():
        fields = line.split(maxsplit=3)
        if len(fields) == 4 and re.fullmatch(re.escape(queue) + r"-[0-9]+", fields[0]):
            job_id, owner, size, submitted = fields
            jobs.append({"id": job_id, "owner": owner, "size": size, "submitted": submitted})
    return jobs


@router.get("/{queue}")
def status(queue: str):
    require_queue(queue)
    detail = cups("lpstat", "-p", queue, "-l")
    first_line = detail.split("\n", 1)[0].removeprefix(f"printer {queue} ").lower()
    return {"state": classify_linux(first_line), "detail": detail, "jobs": active_jobs(queue)}


@router.post("/{queue}/jobs/{job_id}/cancel")
def cancel_job(queue: str, job_id: str):
    require_queue(queue)
    if job_id not in {job["id"] for job in active_jobs(queue)}:
        raise HTTPException(404, "This print job is no longer in the queue.")
    cups("cancel", job_id)
    return status(queue)


@router.post("/{queue}/resume")
def resume(queue: str):
    require_queue(queue)
    cups("cupsenable", queue)
    return status(queue)

@router.post("/{queue}/restart")
def restart_queue(queue: str):
    current = status(queue)
    if current["state"] not in ("ok", "disabled"):
        raise HTTPException(409, "Die Warteschlange kann erst neu gestartet werden, wenn sie bereit oder angehalten ist.")
    if current["state"] == "ok":
        cups("cupsdisable", "-r", "Restart requested by Photobooth", queue)
    try:
        cups("cupsenable", queue)
    except HTTPException as exc:
        raise HTTPException(
            exc.status_code, f"Die Warteschlange konnte nicht wieder freigegeben werden: {exc.detail}"
        ) from exc
    return status(queue)
