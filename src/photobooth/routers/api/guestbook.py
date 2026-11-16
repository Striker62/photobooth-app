from fastapi import APIRouter

from ..api_admin.guestbook import audio, audio_recordings, video, videos

router = APIRouter(prefix="/guestbook", tags=["guestbook playback"])


@router.get("")
def list_recordings():
    return {"audio": audio_recordings(), "video": videos()}


router.add_api_route("/audio/{name}", audio, methods=["GET"])
router.add_api_route("/video/{name}", video, methods=["GET"])
