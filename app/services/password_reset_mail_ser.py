from fastapi_mail import FastMail, MessageSchema, MessageType
from app.core.email_conn import conf


async def send_reset_email(email: str, token: str):

    reset_link = f"http://localhost:3000/reset-password?token={token}"

    message = MessageSchema(
        subject="Password Reset",
        recipients=[email],
        body=f"""
Hello,

You requested a password reset.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you didn't request this, you can ignore this email.
""",
        subtype=MessageType.plain
    )

    fm = FastMail(conf)

    await fm.send_message(message)