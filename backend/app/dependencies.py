from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    현재 사용자 조회 (하이브리드 인증)

    1. Authorization 헤더 우선 (JWT 토큰 - 새 시스템)
    2. X-User-ID 헤더 (레거시 시스템)

    이를 통해 기존 코드와의 호환성을 유지하면서 새 인증 시스템으로 전환할 수 있습니다.
    """
    try:
        # 1. Authorization 헤더 확인 (JWT 토큰 - 새 시스템)
        if authorization:
            # "Bearer " 접두사 제거
            token = authorization.replace("Bearer ", "").strip()

            # JWT 토큰으로 사용자 조회
            from app.services.auth_service import auth_service
            user = await auth_service.get_user_from_token(token, db)

            if user:
                logger.debug(f"User authenticated via JWT: {user.id}")
                return user
            else:
                logger.warning("Invalid JWT token provided")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

        # 2. X-User-ID 헤더 확인 (레거시 시스템)
        if x_user_id:
            result = await db.execute(
                select(User).where(User.id == x_user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                logger.debug(f"User authenticated via X-User-ID: {user.id}")
                return user
            else:
                logger.warning(f"User not found for X-User-ID: {x_user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

        # 3. 인증 정보가 없음
        logger.warning("No authentication credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide either Authorization header or X-User-ID header."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
