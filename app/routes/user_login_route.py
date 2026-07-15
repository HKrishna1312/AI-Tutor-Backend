# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.schemes.user_details import User
# from app.services.user_login_ser import user_check_db
# from app.core.db_session import get_db  
# import logging

# from app.core.config import settings
# from app.core.create_token import token_creation

# from jose import jwt
# from datetime import datetime, timedelta

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# SECRET_KEY = settings.JWT_SECRET_KEY
# ALGORITHM = settings.JWT_ALGORITHM

# router = APIRouter(tags=["Login_user"])

# @router.post("/login")
# async def check_user(email: str, password: str, db: AsyncSession = Depends(get_db)):
#     res = await user_check_db(email=email, password=password, db=db)
#     print("Res", res)
    
#     if res.get("status") == "Login Successful":
#         payload = {
#             "user_id": res.get("user_id", ""),
#         }
#         token = token_creation(data=payload)
        
#         print("Token", token)
#         return {"status": "Login Successful", "token": token}
#     else:
#         return {"status": res, "token": None}


from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemes.user_details import User
from app.services.user_login_ser import user_check_db
from app.core.db_session import get_db  
from app.core.create_token import (
    create_access_token,
    create_refresh_token
)
from app.core.config import settings
import logging

router = APIRouter(tags=["Login_user"])

@router.post("/login")
async def check_user(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):

    res = await user_check_db(
        email=email,
        password=password,
        db=db
    )

    if res.get("status") == "Login Successful":

        payload = {
            "user_id": str(res["user_id"])
        }

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return {
            "status": "Login Successful",
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    return {
        "status": "Login Failed"
    }