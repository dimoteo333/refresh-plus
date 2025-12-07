"""
인증 관련 API 라우트
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    CurrentUserResponse,
    LogoutResponse,
    VerificationStatusResponse
)
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    사용자 로그인

    - 룰루랄라 ID/비밀번호로 로그인
    - Playwright로 실제 룰루랄라 사이트 로그인 (8-10초)
    - JWT 토큰 발급
    - 세션 쿠키 저장

    **주의**: 첫 로그인은 8-10초 소요됩니다.
    """
    try:
        # IP 주소 추출
        ip_address = req.client.host if req and req.client else None

        # 로그인 시도
        result = await auth_service.login(
            username=request.username,
            password=request.password,
            db=db,
            ip_address=ip_address
        )

        # httpOnly 쿠키 설정 (보안)
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            secure=True,  # HTTPS 전용
            samesite="strict",
            max_age=3600  # 1시간
        )

        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=604800  # 7일
        )

        return result

    except ValueError as e:
        # 로그인 실패 (잘못된 인증 정보)
        logger.warning(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        # 계정 잠금
        logger.warning(f"Login denied: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        # 서버 오류
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    현재 로그인한 사용자 정보 조회

    Authorization 헤더에 Bearer 토큰 필요
    """
    user = await auth_service.get_user_from_token(
        token=credentials.credentials,
        db=db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "lulu_lala_user_id": user.lulu_lala_user_id,
            "points": user.points,
            "available_nights": user.available_nights,
            "is_verified": user.is_verified,
            "last_login": user.last_login
        },
        "session_status": "active" if user.is_verified else "pending_verification"
    }


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    액세스 토큰 갱신

    만료된 액세스 토큰을 리프레시 토큰으로 갱신합니다.
    """
    try:
        result = await auth_service.refresh_access_token(
            refresh_token=request.refresh_token,
            db=db
        )

        # 새 액세스 토큰을 쿠키에 저장
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=3600
        )

        return result

    except ValueError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다."
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    로그아웃

    리프레시 토큰을 무효화하고 쿠키를 삭제합니다.
    """
    try:
        await auth_service.logout(
            token=credentials.credentials,
            db=db
        )

        # 쿠키 삭제
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        # 로그아웃은 실패해도 쿠키는 삭제
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return {"message": "Logged out successfully"}


@router.get("/verify-status", response_model=VerificationStatusResponse)
async def check_verification_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    룰루랄라 인증 상태 확인

    백그라운드 인증이 완료되었는지 확인합니다.
    (현재는 동기 로그인을 사용하므로 항상 verified=True)
    """
    user = await auth_service.get_user_from_token(
        token=credentials.credentials,
        db=db
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {
        "is_verified": user.is_verified,
        "failed_attempts": user.failed_login_attempts,
        "locked_until": user.locked_until
    }
