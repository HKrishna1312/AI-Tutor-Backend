from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db_session import get_db  
from app.schemes.password_reset import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.password_reset_ser import (
    create_reset_token,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["Password Reset"])

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    await create_reset_token(db, request.email)

    return {
        "message": "If the account exists, a password reset link has been sent."
    }
    
    
@router.post("/reset-password")
async def reset_password_route(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    success = await reset_password(
        db,
        request.token,
        request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )

    return {
        "message": "Password reset successful."
    }