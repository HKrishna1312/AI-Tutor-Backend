from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager
from app.core.connect_db import async_engine
from app.models.user_details import Base
from sqlalchemy import text

from app.routes import add_user_route, user_login_route, message_route, user_auth_route, password_reset_route, document_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("SELECT 1"))
        print("Application startup complete✅")
    except Exception as e:
        print("Failed to start application ",e)
    yield
    print("Application closed successfully")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



router = [add_user_route.router,
          user_login_route.router, 
          message_route.router, 
          user_auth_route.router, 
          password_reset_route.router,
          document_router.router]

for r in router:
    app.include_router(r)





