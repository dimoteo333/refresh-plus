from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.config import settings

# SQLite 특정 설정
connect_args = {}
if "sqlite" in settings.DATABASE_URL.lower():
    connect_args = {
        "timeout": 30,  # 30초 타임아웃
        "check_same_thread": False,
    }

# 비동기 엔진
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args=connect_args,
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL.lower() else None,
    pool_pre_ping=True
)

# 세션 팩토리
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 별칭 (테스트 스크립트 호환성)
async_session_maker = AsyncSessionLocal

Base = declarative_base()


async def init_db():
    """데이터베이스 초기화 - WAL 모드 활성화"""
    if "sqlite" in settings.DATABASE_URL.lower():
        # SQLite WAL 모드 활성화 (동시 읽기/쓰기 지원)
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=30000"))  # 30초
            await conn.execute(text("PRAGMA synchronous=NORMAL"))


async def get_db() -> AsyncSession:
    """데이터베이스 세션 의존성"""
    async with AsyncSessionLocal() as session:
        yield session
