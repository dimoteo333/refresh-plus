"""
JWT 토큰 생성 및 검증 유틸리티

액세스 토큰과 리프레시 토큰을 생성하고 검증합니다.
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import secrets

from app.config import settings


class JWTError(Exception):
    """JWT 관련 오류"""
    pass


# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1시간
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7일


def _get_secret_key() -> str:
    """
    환경 변수에서 JWT 시크릿 키를 가져옵니다.

    Returns:
        str: JWT 시크릿 키

    Raises:
        JWTError: 시크릿 키가 설정되지 않은 경우
    """
    secret_key = getattr(settings, 'JWT_SECRET_KEY', None)

    if not secret_key:
        raise JWTError("JWT_SECRET_KEY must be set in environment variables")

    return secret_key


def create_access_token(data: Dict) -> str:
    """
    JWT 액세스 토큰 생성

    Args:
        data: 토큰에 포함할 페이로드 데이터 (user_id 필수)

    Returns:
        str: JWT 토큰

    Example:
        >>> token = create_access_token({"user_id": "user_123"})
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    try:
        to_encode = data.copy()

        # 만료 시간 설정
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # JWT 클레임 추가
        to_encode.update({
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "type": "access"  # Token type
        })

        # JWT 인코딩
        secret_key = _get_secret_key()
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

        return encoded_jwt

    except Exception as e:
        raise JWTError(f"Failed to create access token: {str(e)}")


def create_refresh_token(data: Dict) -> Tuple[str, str]:
    """
    JWT 리프레시 토큰 생성

    리프레시 토큰에는 고유한 JTI(JWT ID)가 포함되어 무효화가 가능합니다.

    Args:
        data: 토큰에 포함할 페이로드 데이터 (user_id 필수)

    Returns:
        Tuple[str, str]: (토큰, JTI)

    Example:
        >>> token, jti = create_refresh_token({"user_id": "user_123"})
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
        >>> print(jti)
        'abc123def456...'
    """
    try:
        to_encode = data.copy()

        # 만료 시간 설정 (7일)
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # 고유한 JTI 생성 (토큰 무효화에 사용)
        jti = secrets.token_urlsafe(32)

        # JWT 클레임 추가
        to_encode.update({
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "jti": jti,  # JWT ID
            "type": "refresh"  # Token type
        })

        # JWT 인코딩
        secret_key = _get_secret_key()
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

        return encoded_jwt, jti

    except Exception as e:
        raise JWTError(f"Failed to create refresh token: {str(e)}")


def verify_token(token: str, token_type: str = "access") -> Dict:
    """
    JWT 토큰 검증

    Args:
        token: JWT 토큰
        token_type: "access" 또는 "refresh"

    Returns:
        Dict: 디코딩된 페이로드

    Raises:
        JWTError: 토큰이 유효하지 않거나 만료된 경우

    Example:
        >>> token = create_access_token({"user_id": "user_123"})
        >>> payload = verify_token(token)
        >>> print(payload["user_id"])
        'user_123'
    """
    try:
        secret_key = _get_secret_key()

        # JWT 디코딩
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

        # 토큰 타입 검증
        if payload.get("type") != token_type:
            raise JWTError(f"Expected {token_type} token, but got {payload.get('type')}")

        return payload

    except jwt.ExpiredSignatureError:
        raise JWTError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise JWTError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise JWTError(f"Token verification failed: {str(e)}")


def decode_token_unsafe(token: str) -> Optional[Dict]:
    """
    토큰을 검증 없이 디코딩 (디버깅 용도)

    주의: 프로덕션 코드에서 사용하지 마세요!

    Args:
        token: JWT 토큰

    Returns:
        Dict | None: 디코딩된 페이로드 (실패 시 None)
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except Exception:
        return None


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    토큰의 만료 시간 조회

    Args:
        token: JWT 토큰

    Returns:
        datetime | None: 만료 시간 (검증 실패 시 None)
    """
    try:
        payload = verify_token(token)
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        return None
    except JWTError:
        return None


def is_token_expired(token: str) -> bool:
    """
    토큰이 만료되었는지 확인

    Args:
        token: JWT 토큰

    Returns:
        bool: 만료되었으면 True
    """
    try:
        verify_token(token)
        return False
    except JWTError as e:
        if "expired" in str(e).lower():
            return True
        return False


def verify_jwt_settings() -> bool:
    """
    JWT 설정이 올바른지 확인

    Returns:
        bool: 설정이 올바르면 True
    """
    try:
        _get_secret_key()
        return True
    except JWTError:
        return False


# 테스트 함수 (개발 용도)
def _test_jwt():
    """JWT 생성/검증 라운드트립 테스트"""
    test_data = {
        "user_id": "user_123",
        "lulu_lala_user_id": "lulu_user_456"
    }

    print("=== JWT Test ===")

    # 액세스 토큰 테스트
    print("\n1. Access Token:")
    access_token = create_access_token(test_data)
    print(f"   Token: {access_token[:50]}...")
    print(f"   Length: {len(access_token)}")

    payload = verify_token(access_token, token_type="access")
    print(f"   Verified payload: {payload}")
    assert payload["user_id"] == test_data["user_id"]
    print("   ✓ Access token test passed!")

    # 리프레시 토큰 테스트
    print("\n2. Refresh Token:")
    refresh_token, jti = create_refresh_token(test_data)
    print(f"   Token: {refresh_token[:50]}...")
    print(f"   JTI: {jti}")

    payload = verify_token(refresh_token, token_type="refresh")
    print(f"   Verified payload: {payload}")
    assert payload["user_id"] == test_data["user_id"]
    assert payload["jti"] == jti
    print("   ✓ Refresh token test passed!")

    # 만료 시간 테스트
    print("\n3. Token Expiration:")
    exp_time = get_token_expiration(access_token)
    print(f"   Access token expires at: {exp_time}")
    print(f"   Is expired: {is_token_expired(access_token)}")

    # 잘못된 토큰 타입 테스트
    print("\n4. Invalid Token Type:")
    try:
        verify_token(access_token, token_type="refresh")
        print("   ✗ Should have failed!")
    except JWTError as e:
        print(f"   ✓ Correctly rejected: {e}")

    print("\n=== All JWT tests passed! ===")


if __name__ == "__main__":
    # 스크립트로 직접 실행 시 테스트
    _test_jwt()
