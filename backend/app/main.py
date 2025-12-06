from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routes import accommodations, bookings, users, wishlist, notifications, scores, chatbot
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Sentry 초기화 (선택적)
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=1.0,
            environment=settings.ENVIRONMENT
        )
except ImportError:
    logger.warning("Sentry SDK not installed. Skipping Sentry initialization.")

# DB 테이블 생성 (Alembic 사용 시 주석 처리)
# AsyncEngine은 create_all을 지원하지 않으므로 Alembic migration 사용
# Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup")
    yield
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(
    title="Refresh Plus API",
    description="Employee Accommodation Booking System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip 압축
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 헬스 체크
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT
    }

# 라우터 등록
app.include_router(
    accommodations.router,
    prefix="/api/accommodations",
    tags=["accommodations"]
)
app.include_router(
    bookings.router,
    prefix="/api/bookings",
    tags=["bookings"]
)
app.include_router(
    users.router,
    prefix="/api/users",
    tags=["users"]
)
app.include_router(
    wishlist.router,
    prefix="/api/wishlist",
    tags=["wishlist"]
)
app.include_router(
    notifications.router,
    prefix="/api/notifications",
    tags=["notifications"]
)
app.include_router(
    scores.router,
    prefix="/api/scores",
    tags=["scores"]
)
app.include_router(
    chatbot.router,
    prefix="/api/chatbot",
    tags=["chatbot"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
