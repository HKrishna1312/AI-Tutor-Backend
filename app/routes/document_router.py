
from fastapi import APIRouter, UploadFile, File, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_service import process_document
from app.core.verify_token import verify_access_token
from app.core.db_session import get_db


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db)
):
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

    result = await process_document(
        file=file,
        user_id=user_id,
        db=db
    )

    return result