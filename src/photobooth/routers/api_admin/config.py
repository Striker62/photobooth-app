import logging
from typing import Any, AnyStr

from fastapi import APIRouter, Body, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic_core import ValidationError

from ...appconfig import appconfig
from ...container import container
from ...services.config.groups.cameras import GroupCameraPicamera2, PicameraLightProfile, PicameraLightSettings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["admin", "config"])


@router.get("/list")
def api_get_configurables():
    return container.config_service.list_configurables()


@router.delete("")
def api_reset_all_config():
    raise NotImplementedError


@router.delete("/{configurable}")
def api_reset_config(configurable: str):
    container.config_service.reset(configurable)


def light_camera(index: int) -> tuple[int, GroupCameraPicamera2]:
    enabled = [(i, entry.backend_config) for i, entry in enumerate(appconfig.cameras.group_backends) if entry.enabled]
    if index < 0 or index >= len(enabled):
        raise HTTPException(404, "Kamera nicht gefunden.")
    position, camera = enabled[index]
    if not isinstance(camera, GroupCameraPicamera2):
        raise HTTPException(400, "Die Lichtprofile benötigen eine Picamera2-Kamera.")
    return position, camera


@router.get("/light/{index}")
def get_light_settings(index: int):
    _, camera = light_camera(index)
    return {
        "settings": camera.model_dump(include=set(PicameraLightSettings.model_fields)),
        "profiles": camera.light_profiles,
        "trial": container.acquisition_service.get_light_trial(index),
    }


@router.put("/light/{index}/trial")
def set_light_trial(index: int, settings: PicameraLightSettings | None = Body(default=None)):
    light_camera(index)
    try:
        container.acquisition_service.set_light_trial(index, settings)
    except (RuntimeError, IndexError, OSError, ValueError) as exc:
        raise HTTPException(409, "Die Kamera konnte die Testwerte gerade nicht übernehmen.") from exc
    return {"testing": settings is not None}


@router.put("/light/{index}")
def save_light_settings(index: int, settings: PicameraLightSettings):
    position, _ = light_camera(index)
    config = container.config_service.get_current("app", True)
    config["cameras"]["group_backends"][position]["backend_config"].update(settings.model_dump())
    container.config_service.validate_and_set_current_and_persist("app", config)
    container.reload()
    return get_light_settings(index)


@router.post("/light/{index}/profiles")
def save_light_profile(index: int, profile: PicameraLightProfile):
    position, camera = light_camera(index)
    config = container.config_service.get_current("app", True)
    profiles = [item.model_dump() for item in camera.light_profiles if item.name != profile.name]
    profiles.append(profile.model_dump())
    config["cameras"]["group_backends"][position]["backend_config"]["light_profiles"] = profiles
    container.config_service.validate_and_set_current_and_persist("app", config)
    return get_light_settings(index)


@router.get("/{configurable}/schema")
def api_get_config_schema(configurable: str):
    return container.config_service.get_schema(configurable)


@router.get("/{configurable}")
def api_get_config_current_active(configurable: str):
    return container.config_service.get_current(configurable, True)


@router.patch("/{configurable}")
def api_post_config_current(configurable: str, updated_config: dict[AnyStr, Any], reload: bool = False):
    """Update the configuration for appconfig (configurable=app) or a plugin (example configurable="photobooth.plugins.gpio_lights")
    The configuration is persisted also after update.
    updated_config is a generic type valid to receive json objects instead of a pydantic model because depending on the configurable
    the model is different.

    Args:
        configurable (str): app for appconfig, otherwise str with plugin name to update the config for. Defaults to None.
        updated_config (dict[AnyStr, Any]): valid json that is validated against appconfig or plugin config pydantic models
    """

    # persists also automatically
    try:
        container.config_service.validate_and_set_current_and_persist(configurable, updated_config)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    if reload:
        logger.info("reload parameter is set, so all registered services are reloaded now. This may take some time...")
        container.reload()
