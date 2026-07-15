from datetime import datetime, timedelta
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_details import UserTable
from app.models.password_reset import PasswordResetToken
from app.core.hash_password import hash_password
from datetime import datetime
from app.services.password_reset_mail_ser import send_reset_email

async def create_reset_token(db: Session, email: str):
    result = await db.execute(
        select(UserTable).where(UserTable.email == email)
    )

    user = result.scalar_one_or_none()

    if user is None:
        return None

    token = secrets.token_urlsafe(32)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        used=False
    )

    db.add(reset_token)
    await db.commit()
    
    await send_reset_email(user.email, token)

    return token




async def verify_reset_token(db: Session, token: str):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token
        )
    )

    reset = result.scalar_one_or_none()

    if reset is None:
        return None

    if reset.used:
        return None

    if reset.expires_at < datetime.utcnow():
        return None

    return reset




async def reset_password(db: Session, token: str, new_password: str):

    reset = await verify_reset_token(db, token)

    if reset is None:
        return False

    result = await db.execute(
        select(UserTable).where(UserTable.id == reset.user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        return False

    user.password = hash_password(new_password)

    reset.used = True

    await db.commit()

    return True