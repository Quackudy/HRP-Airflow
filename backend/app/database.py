import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Detect SQLite and build async URL for it
_is_sqlite = DATABASE_URL.startswith("sqlite://")
if _is_sqlite:
    SYNC_DATABASE_URL = DATABASE_URL
    # convert sqlite:///./dev.db -> sqlite+aiosqlite:///./dev.db
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
else:
    SYNC_DATABASE_URL = DATABASE_URL
    # for postgres: postgresql:// -> postgresql+asyncpg://
    if DATABASE_URL.startswith("postgresql://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        ASYNC_DATABASE_URL = DATABASE_URL

# Sync engine (used by Alembic or any sync code)
_sync_connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True, connect_args=_sync_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine & session (used by FastAPI async endpoints)
_async_connect_args = {"check_same_thread": False} if _is_sqlite else {}
async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args=_async_connect_args)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Sync dependency (if you have sync endpoints)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Async dependency for async endpoints
async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
