from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.config import settings

import libsql_experimental

# Binary 속성 추가
if not hasattr(libsql_experimental, 'Binary'):
    libsql_experimental.Binary = bytes

def _build_engine():
    """
    Turso(libsql)와 로컬 sqlite(aiosqlite) 경로를 분리해 엔진을 생성한다.
    - libsql: 메인 DB (Turso)
    - sqlite+aiosqlite: 로컬 개발용만 허용
    """
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured.")


    url = make_url(settings.DATABASE_URL)
    driver = url.drivername

    # Turso (libsql) 메인 DB
    if driver.startswith("libsql"):
        # SQLAlchemy libsql 드라이버 네이밍에 맞게 보정
        # - async: sqlite+aiolibsql
        # - secure 채널 기본값: True (https/wss)
        url = url.set(drivername="sqlite+aiolibsql")
        query = dict(url.query)
        query.setdefault("secure", "true")
        url = url.set(query=query)

        connect_args = {}
        if settings.DATABASE_AUTH_TOKEN:
            connect_args["auth_token"] = settings.DATABASE_AUTH_TOKEN

        return create_async_engine(
            url,
            echo=settings.DEBUG,
            future=True,
            connect_args=connect_args,
            pool_pre_ping=True,
            poolclass=NullPool  # SQLite 기반 드라이버는 NullPool 사용
        )

    # 로컬 개발용 sqlite (aiosqlite 전용)
    if driver.startswith("sqlite"):
        # aiosqlite를 강제하여 메인 DB와 분리
        if driver != "sqlite+aiosqlite":
            url = url.set(drivername="sqlite+aiosqlite")

        return create_async_engine(
            url,
            echo=settings.DEBUG,
            future=True,
            connect_args={"timeout": 30, "check_same_thread": False},
            poolclass=NullPool,
            pool_pre_ping=True
        )

    # 기타 드라이버 (예: postgres 등)
    return create_async_engine(
        url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True
    )


# 비동기 엔진
engine = _build_engine()

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
    db_url = str(engine.url)

    async with engine.begin() as conn:
        # ✅ 진짜 로컬 sqlite(aioSQLite)일 때만 PRAGMA 실행
        if "aiosqlite" in db_url:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA busy_timeout=30000"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))



async def get_db() -> AsyncSession:
    """데이터베이스 세션 의존성"""
    async with AsyncSessionLocal() as session:
        yield session
