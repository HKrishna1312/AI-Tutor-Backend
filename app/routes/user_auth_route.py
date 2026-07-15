from fastapi import APIRouter, HTTPException
from jose import jwt, JWTError

from app.core.config import settings
from app.core.create_token import (
    create_access_token,
    create_refresh_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/refresh")
async def refresh_tokens(refresh_token: str):

    try:

        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )

        user_id = payload.get("user_id")

        new_payload = {
            "user_id": user_id
        }

        new_access_token = create_access_token(
            new_payload
        )

        new_refresh_token = create_refresh_token(
            new_payload
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token expired. Login again."
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )