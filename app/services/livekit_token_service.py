
from livekit import api
from fastapi import HTTPException
from sqlalchemy import select
from app.core.config import settings
from app.core.connect_db import AsyncSessionLocal
from app.models.user_details import UserTable
from app.models.resume_vectors import ResumeVectorTable
import json
import logging

logger = logging.getLogger(__name__)


async def get_user_name(user_id: str) -> str:
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserTable).where(UserTable.id == int(user_id))
            )
            user = result.scalar_one_or_none()
    except Exception:
        logger.warning(f"Could not fetch name for user_id '{user_id}'")
        return str(user_id)

    if not user:
        return str(user_id)

    return user.username or str(user_id)


async def get_latest_vector_id(user_id: str) -> str | None:
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ResumeVectorTable)
                .where(ResumeVectorTable.user_id == str(user_id))
                .order_by(ResumeVectorTable.created_at.desc())
                .limit(1)
            )
            record = result.scalar_one_or_none()
    except Exception:
        logger.warning(f"Could not fetch vector id for user_id '{user_id}'")
        return None

    if not record:
        return None

    return record.vector_id


async def get_token(
    room_name: str = "my-room",
    participant_name: str = "",
    user_id: str = "",
) -> dict[str, str]:
    livekit_url = settings.LIVEKIT_URL
    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET
    if not livekit_url or not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="LiveKit server is not configured")

    if not user_id or not str(user_id).strip():
        raise HTTPException(status_code=401, detail="User ID missing from token")

    user_id = str(user_id)
    display_name = participant_name or await get_user_name(user_id)
    vector_id = await get_latest_vector_id(user_id)

    if not vector_id:
        logger.warning(f"No resume vectors found for user_id '{user_id}'")

    try:
        token = (
            api.AccessToken(api_key, api_secret)
            .with_identity(user_id)
            .with_name(display_name)
            .with_metadata(
                json.dumps(
                    {
                        "user_id": user_id,
                        "user_name": display_name,
                        "vector_id": vector_id
                    }
                )
            )
            .with_grants(api.VideoGrants(room_join=True, room=room_name))
        )
        logger.info(
            f"Generated LiveKit token for user_id '{user_id}' "
            f"with name '{display_name}' and vector_id '{vector_id}' "
            f"in room '{room_name}'"
        )
        return {
            "token": token.to_jwt(),
            "url": livekit_url,
            "room": room_name,
            "user_id": user_id,
            "user_name": display_name,
            "vector_id": vector_id
        }
    except Exception as error:
        logger.error("Failed to create LiveKit token")
        raise HTTPException(status_code=500, detail="Could not create LiveKit token") from error
