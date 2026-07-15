# from jose import jwt
# from datetime import datetime, timedelta
# from .config import settings

# SECRET_KEY = settings.JWT_SECRET_KEY
# ALGORITHM = settings.JWT_ALGORITHM


# async def token_creation(data: dict):
# # Add custom payload
#     payload_1 = {
#     "user_id": data.get("user_id", ""),  
#     "type": "access",
#     "exp": datetime.utcnow() + timedelta(minutes=1)  # expiration
# }
#     payload_2 = {
#     "user_id": data.get("user_id", ""),  
#     "type": "refresh",
#     "exp": datetime.utcnow() + timedelta(minutes=1)  # expiration
# }

# # Encode JWT
#     access_token = jwt.encode(payload_1, SECRET_KEY, algorithm=ALGORITHM)
#     refresh_token = jwt.encode(payload_2, SECRET_KEY, algorithm=ALGORITHM)
#     return {"access_token": access_token, "refresh_token": refresh_token}

# create_token.py

from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings
import logging
logger = logging.getLogger(__name__)


SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

def create_access_token(data: dict):
    logger.info("Inside Create Access Token")
    payload = data.copy()

    payload.update({
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=1)
    })

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(data: dict):
    logger.info("Inside Create Refresh Token")
    payload = data.copy()

    payload.update({
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    })

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )