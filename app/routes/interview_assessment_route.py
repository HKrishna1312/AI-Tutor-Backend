from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.core.verify_token import verify_access_token
from app.schemes.interview_assessment import (
    ProcessInterviewRequest,
    ProcessInterviewResponse,
)
from app.services import interview_assessment_service as service


router = APIRouter(prefix="/interviews", tags=["Interview Assessment"])


async def current_user_id(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    payload = await verify_access_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID missing from token")
    return str(user_id)


@router.post("/process", response_model=ProcessInterviewResponse, status_code=status.HTTP_201_CREATED)
async def process_interview(
    payload: ProcessInterviewRequest,
    user_id: str = Depends(current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.process_completed_interview(db, user_id, payload.title, payload.transcript)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
