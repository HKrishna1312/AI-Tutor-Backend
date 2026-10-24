from fastapi import APIRouter, Header, Query, HTTPException
from fastapi.responses import JSONResponse

from app.core.verify_token import verify_access_token
from app.services.livekit_token_service import get_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/livekit", tags=["LiveKit Token"])


@router.get("/token", response_class=JSONResponse)
async def get_livekit_token(
    authorization: str = Header(...),
    room_name: str = Query("my-room", description="Room the user should join")
):
    """
    Generate a LiveKit access token for the logged in user.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    access_token = authorization.split(" ", 1)[1]

    payload = await verify_access_token(access_token)

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID missing from token"
        )

    try:
        return await get_token(
            room_name=room_name,
            participant_name=payload.get("username", ""),
            user_id=str(user_id)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating LiveKit token: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate token: {str(e)}"
        )
