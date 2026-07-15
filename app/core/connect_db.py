# from sqlalchemy import create_engine
# from app.core.config import Settings

# settings = Settings()

# async def create_connection():
#     username = settings.DB_USER
#     password = settings.DB_PASS
#     database_name = settings.DB_NAME

#     # Example using pymysql
#     connection_url = f"mysql+pymysql://{username}:{password}@localhost:3306/{database_name}"
#     engine = create_engine(connection_url)
#     return engine



from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings

settings = Settings()

def create_connection():
    username = settings.DB_USER
    password = settings.DB_PASS
    database_name = settings.DB_NAME

    connection_url = (
        f"mysql+aiomysql://{username}:{password}@localhost:3306/{database_name}"
    )

    engine = create_async_engine(connection_url, echo=True, future=True)
    return engine

# Create session factory
async_engine = create_connection()
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

from sqlalchemy.orm import declarative_base

Base = declarative_base()