# from sqlalchemy.orm import sessionmaker
# from app.core.connect_db import create_connection
# from app.schemes.user_details import User
# from app.models.user_details import UserTable
# import logging

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# async def add_user_db(user_data: User):
#     try:
#         engine = await create_connection()
#         SessionLocal = sessionmaker(bind=engine)
#         session = SessionLocal()

#         new_user = UserTable(
#             username=user_data.username,
#             email=user_data.email,
#             password=user_data.password
#         )

#         session.add(new_user)
#         session.commit()
#         session.refresh(new_user)
#         session.close()
#         logger.info("User Added")
#         return "User Added"
    
#     except Exception as e:
#         logger.error(e)
#         return f"Error while adding user {e}"

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemes.user_details import User
from app.models.user_details import UserTable
from app.core.hash_password import hash_password
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def add_user_db(user_data: User, db: AsyncSession):
    try:
        new_user = UserTable(
            username=user_data.username,
            email=user_data.email,
            password=hash_password(user_data.password)
        )

        db.add(new_user)
        await db.commit()          # <-- MUST use await
        await db.refresh(new_user) # <-- MUST use await
        logger.info("User Added")
        return new_user
    
    except Exception as e:
        logger.error("Error while adding user ", e)
        return f"Error while adding user {e}"