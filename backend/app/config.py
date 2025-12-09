from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator
import json

class Settings(BaseSettings):
    # 기본 설정
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PROJECT_NAME: str = "Refresh Plus"

    # 데이터베이스
    DATABASE_URL: str = "sqlite+aiosqlite:///./refresh_plus.db"

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str | None = None
    FIREBASE_PROJECT_ID: str | None = None

    # Kakao Talk
    KAKAO_REST_API_KEY: str
    KAKAO_CHANNEL_ID: str

    # AWS
    AWS_REGION: str = "ap-northeast-2"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Redis (캐시)
    REDIS_URL: str | None = None

    # Sentry
    SENTRY_DSN: str | None = None

    # CORS
    CORS_ORIGINS: str | List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """CORS_ORIGINS를 JSON 문자열 또는 리스트로 파싱"""
        if isinstance(v, str):
            try:
                # JSON 배열 형태의 문자열인 경우 파싱
                return json.loads(v)
            except json.JSONDecodeError:
                # 단일 URL 문자열인 경우 리스트로 변환
                return [v]
        return v

    # 애플리케이션 설정
    MAX_WISHLIST_ITEMS: int = 20
    POINTS_PER_BOOKING: int = 10
    POINTS_RECOVERY_HOURS: int = 24
    MAX_POINTS: int = 100

    # RAG 설정
    RAG_MODEL: str = "gpt-4o-mini"
    RAG_TEMPERATURE: float = 0.7
    OPENAI_API_KEY: str | None = None

    # 암호화 설정
    ENCRYPTION_MASTER_KEY: str | None = None
    ENCRYPTION_SALT: str | None = None
    JWT_SECRET_KEY: str | None = None

    # Lulu-Lala 크롤링 설정
    LULU_LALA_USERNAME: str | None = None
    LULU_LALA_PASSWORD: str | None = None
    LULU_LALA_RSA_PUBLIC_KEY: str | None = None

    # Web Push (VAPID) 설정
    VAPID_PUBLIC_KEY: str | None = None
    VAPID_PRIVATE_KEY: str | None = None
    VAPID_EMAIL: str = "noreply@refreshplus.com"

    @field_validator('LULU_LALA_RSA_PUBLIC_KEY', mode='before')
    @classmethod
    def normalize_rsa_key(cls, v):
        """RSA 공개키의 \n을 실제 줄바꿈으로 변환"""
        if v and isinstance(v, str):
            # \n을 실제 줄바꿈으로 변환
            return v.replace('\\n', '\n')
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 추가 환경 변수 허용

settings = Settings()
