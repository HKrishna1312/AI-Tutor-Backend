
import json

from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_service import process_document
from app.core.verify_token import verify_access_token
from app.core.db_session import get_db
from app.models.resume_vectors import ResumeVectorTable


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


async def _user_from_auth(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required; use Bearer <access_token>"
        )

    scheme, _, access_token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not access_token.strip():
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header; use Bearer <access_token>"
        )

    payload = await verify_access_token(access_token)

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID missing from token"
        )

    return str(user_id)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db)
):
    user_id = await _user_from_auth(authorization)

    result = await process_document(
        file=file,
        user_id=user_id,
        db=db
    )

    return result


@router.get("/resume")
async def get_resume(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db)
):
    user_id = await _user_from_auth(authorization)

    result = await db.execute(
        select(ResumeVectorTable)
        .where(ResumeVectorTable.user_id == user_id)
        .order_by(ResumeVectorTable.created_at.desc(), ResumeVectorTable.id.desc())
        .limit(1)
    )
    record = result.scalars().first()

    if not record:
        return {"has_resume": False}

    profile = None
    if record.profile:
        try:
            profile = json.loads(record.profile)
        except (TypeError, ValueError):
            profile = None

    return {
        "has_resume": True,
        "filename": record.filename,
        "vector_id": record.vector_id,
        "uploaded_at": record.created_at.isoformat() if record.created_at else None,
        "profile": profile
    }