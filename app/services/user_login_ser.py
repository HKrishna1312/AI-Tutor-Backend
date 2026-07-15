from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemes.user_details import User
from app.models.user_details import UserTable
from app.core.hash_password import verify_password
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# async def user_check_db(email: str, password: str, db: AsyncSession):
#     try:
#         # Query to check if user exists with provided credentials
#         query = select(UserTable).where(
#             (UserTable.email == email) & (UserTable.password == password)
#         )
        
#         result = await db.execute(query)
#         user = result.scalar_one_or_none()
#         logger.info(f"User details while login: {user}")
#         if user:
#             logger.info(f"Login successful for user: {user.username}")
#             logger.info("Login Succesfull")
#             return {
#                 "status": "Login Successful",
#                 "user_id": user.id,
#                 "username": user.username,
#                 "email": user.email
#             }
#         else:
#             logger.warning(f"Login failed for user: {email}")
#             return {
#                 "status": "Login Failed",
#                 "message": "Invalid username or password"
#             }
    
#     except Exception as e:
#         logger.error("Error while checking user login", e)
#         return {
#             "status": "Login Failed",
#             "message": f"Error during login process: {str(e)}"
#         }

async def user_check_db(email: str, password: str, db: AsyncSession):
    try:
        query = select(UserTable).where(UserTable.email == email)

        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return {
                "status": "Login Failed",
                "message": "Invalid email or password"
            }

        if not verify_password(password, user.password):
            return {
                "status": "Login Failed",
                "message": "Invalid email or password"
            }

        logger.info(f"Login successful for {user.username}")

        return {
            "status": "Login Successful",
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }

    except Exception:
        logger.exception("Error while checking user login")
        return {
            "status": "Login Failed",
            "message": "Error during login process"
        }