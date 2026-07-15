# from fastapi import APIRouter
# from app.schemes.user_details import User
# from app.services.add_user_ser import add_user_db
# import logging

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)


# router = APIRouter(tags=["New_user"])


# @router.post("/new_user")
# async def add_new_user(user_data: User):
#     try:
#         res = await add_user_db(user_data=user_data)
#         logger.info(res)
#         return {"status":res}
#     except Exception as e:
#         logger.error(e)
#         return {"status":e}




from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemes.user_details import User
from app.services.add_user_ser import add_user_db
from app.core.db_session import get_db  
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



router = APIRouter(tags=["New_user"])

@router.post("/new_user")
async def add_new_user(
    user_data: User, 
    db: AsyncSession = Depends(get_db)  
):
    res = await add_user_db(user_data=user_data, db=db)
    return {"status": res}
