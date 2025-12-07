"""
인증 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str = Field(..., description="룰루랄라 사용자 ID", min_length=3, max_length=100)
    password: str = Field(..., description="룰루랄라 비밀번호", min_length=4, max_length=100)

    @validator('username')
    def username_alphanumeric(cls, v):
        """사용자명은 영문자, 숫자, 일부 특수문자만 허용"""
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError('Username must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v


class UserInfo(BaseModel):
    """사용자 정보 (응답용)"""
    id: str
    name: Optional[str]
    lulu_lala_user_id: Optional[str]
    points: float
    available_nights: int
    is_verified: bool
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """로그인 응답"""
    access_token: str = Field(..., description="JWT 액세스 토큰 (1시간 유효)")
    refresh_token: str = Field(..., description="리프레시 토큰 (7일 유효)")
    token_type: str = "bearer"
    user: UserInfo = Field(..., description="사용자 정보")


class RefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., description="리프레시 토큰")


class RefreshResponse(BaseModel):
    """토큰 갱신 응답"""
    access_token: str = Field(..., description="새 액세스 토큰")
    token_type: str = "bearer"


class VerificationStatusResponse(BaseModel):
    """룰루랄라 인증 상태 응답"""
    is_verified: bool = Field(..., description="인증 완료 여부")
    failed_attempts: int = Field(..., description="실패 횟수")
    locked_until: Optional[datetime] = Field(None, description="계정 잠금 해제 시간")


class LogoutResponse(BaseModel):
    """로그아웃 응답"""
    message: str = "Logged out successfully"


class CurrentUserResponse(BaseModel):
    """현재 사용자 정보 응답"""
    user: UserInfo
    session_status: str = Field(..., description="세션 상태 (active/expired 등)")


# 에러 응답 스키마
class ErrorResponse(BaseModel):
    """에러 응답"""
    detail: str = Field(..., description="에러 메시지")


class ValidationErrorResponse(BaseModel):
    """검증 오류 응답"""
    detail: list = Field(..., description="검증 오류 목록")
