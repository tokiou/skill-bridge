from app.shared.config.settings import Settings
from app.shared.db.base import Base
from functools import lru_cache
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os
from dotenv import load_dotenv


load_dotenv()
@lru_cache
def get_settings():
    return Settings()


engine = create_async_engine(
    os.environ['DATABASE_URL'],
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

