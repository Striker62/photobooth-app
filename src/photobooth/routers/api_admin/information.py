import logging
import json
import re
from importlib.metadata import PackageNotFoundError, distribution

from fastapi import APIRouter, HTTPException, status

from ...container import container

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/information", tags=["admin", "information"])


@router.get("/revision")
def installed_revision() -> dict[str, str | None]:
    try:
        metadata = json.loads(distribution("photobooth-app").read_text("direct_url.json") or "{}")
    except (PackageNotFoundError, OSError, ValueError):
        return {"commit": None}
    vcs = metadata.get("vcs_info", {}) if isinstance(metadata, dict) else {}
    commit = vcs.get("commit_id") if isinstance(vcs, dict) and vcs.get("vcs") == "git" else None
    return {"commit": commit[:7] if isinstance(commit, str) and re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", commit) else None}


@router.get("/cntr/reset/{field}", status_code=status.HTTP_204_NO_CONTENT)  # it's cntr because statscounter is blocked by adblocker often
def api_get_statscounter_reset_field(field: str):
    """ """
    try:
        container.information_service.stats_counter_reset(field)
    except Exception as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"failed to reset stats, error {exc}") from exc


@router.get("/cntr/reset/", status_code=status.HTTP_204_NO_CONTENT)  # it's cntr because statscounter is blocked by adblocker often
def api_get_statscounter_reset_all():
    """ """
    try:
        container.information_service.stats_counter_reset_all()
    except Exception as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"failed to reset stats, error {exc}") from exc
