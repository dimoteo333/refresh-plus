from sqlalchemy import Column, String, Integer, DateTime, Boolean, LargeBinary, JSON, Float
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """
    사용자 정보
    """
    __tablename__ = "users"

    # 기본 정보
    id = Column(String, primary_key=True, index=True)  # 사용자 ID (PK)
    name = Column(String)  # 사용자명
    points = Column(Float, default=100.0)  # 점수 (소수점 지원)
    available_nights = Column(Integer, default=0)  # 사용가능박수

    # 인증 관련
    lulu_lala_user_id = Column(String, unique=True, index=True, nullable=True)  # 룰루랄라 사용자 ID
    encrypted_password = Column(LargeBinary, nullable=True)  # AES-256 암호화된 비밀번호
    encryption_key_version = Column(Integer, default=1)  # 키 로테이션용

    # 세션 관리
    session_cookies = Column(JSON, nullable=True)  # 룰루랄라 세션 쿠키
    session_expires_at = Column(DateTime, nullable=True)  # 세션 만료 시간
    last_login = Column(DateTime, nullable=True)  # 마지막 로그인

    # 보안
    is_active = Column(Boolean, default=True)  # 계정 활성화 상태
    is_verified = Column(Boolean, default=False)  # 룰루랄라 인증 완료 여부
    failed_login_attempts = Column(Integer, default=0)  # 실패 횟수
    locked_until = Column(DateTime, nullable=True)  # 잠금 해제 시간

    # 리프레시 토큰
    refresh_token_jti = Column(String, nullable=True, index=True)  # 리프레시 토큰 ID
    refresh_token_expires_at = Column(DateTime, nullable=True)  # 리프레시 토큰 만료

    # 타임스탬프
    created_at = Column(DateTime, default=func.now())  # 등록시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 업데이트시간
