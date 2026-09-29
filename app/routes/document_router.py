
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
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
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

    result = await process_document(
        file=file,
        user_id=user_id,
        db=db
    )

    return result