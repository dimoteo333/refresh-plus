"""
비밀번호 암호화/복호화 유틸리티

AES-256-GCM을 사용하여 룰루랄라 비밀번호를 안전하게 저장합니다.
복호화가 필요한 이유: Playwright를 통한 룰루랄라 로그인 시 평문 비밀번호 필요
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import secrets
from typing import Optional

from app.config import settings


class EncryptionError(Exception):
    """암호화 관련 오류"""
    pass


# 마스터 키에서 암호화 키 유도
def _derive_key(master_key: bytes, salt: bytes) -> bytes:
    """
    PBKDF2를 사용하여 마스터 키에서 암호화 키 유도

    Args:
        master_key: 마스터 키 (환경 변수)
        salt: 솔트 (환경 변수)

    Returns:
        bytes: 256-bit 암호화 키
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits for AES-256
        salt=salt,
        iterations=100000,  # OWASP 권장 최소값
    )
    return kdf.derive(master_key)


# 환경 변수에서 키 로드
def _get_encryption_key() -> bytes:
    """
    환경 변수에서 암호화 키를 가져옵니다.

    Returns:
        bytes: 256-bit 암호화 키

    Raises:
        EncryptionError: 환경 변수가 설정되지 않은 경우
    """
    master_key = getattr(settings, 'ENCRYPTION_MASTER_KEY', None)
    salt = getattr(settings, 'ENCRYPTION_SALT', None)

    if not master_key or not salt:
        raise EncryptionError(
            "ENCRYPTION_MASTER_KEY and ENCRYPTION_SALT must be set in environment variables"
        )

    # 문자열을 바이트로 변환
    master_key_bytes = master_key.encode('utf-8') if isinstance(master_key, str) else master_key
    salt_bytes = salt.encode('utf-8') if isinstance(salt, str) else salt

    return _derive_key(master_key_bytes, salt_bytes)


def encrypt_password(password: str) -> bytes:
    """
    AES-256-GCM으로 비밀번호 암호화

    Args:
        password: 평문 비밀번호

    Returns:
        bytes: nonce (12 bytes) + ciphertext + auth_tag (16 bytes)

    Example:
        >>> encrypted = encrypt_password("my_password")
        >>> len(encrypted)  # nonce(12) + ciphertext + tag(16)
        40  # 대략적인 크기 (비밀번호 길이에 따라 다름)
    """
    try:
        # 암호화 키 가져오기
        key = _get_encryption_key()

        # AES-GCM 암호화 객체 생성
        aesgcm = AESGCM(key)

        # 랜덤 nonce 생성 (96-bit for GCM)
        nonce = secrets.token_bytes(12)

        # 암호화 수행
        # GCM 모드는 자동으로 인증 태그(16 bytes)를 ciphertext에 포함
        ciphertext = aesgcm.encrypt(
            nonce,
            password.encode('utf-8'),
            None  # No associated data
        )

        # nonce와 ciphertext를 결합하여 반환
        # Format: nonce(12 bytes) || ciphertext || auth_tag(16 bytes)
        return nonce + ciphertext

    except Exception as e:
        raise EncryptionError(f"Failed to encrypt password: {str(e)}")


def decrypt_password(encrypted: bytes) -> str:
    """
    암호화된 비밀번호 복호화

    Args:
        encrypted: nonce (12 bytes) + ciphertext + auth_tag (16 bytes)

    Returns:
        str: 복호화된 평문 비밀번호

    Raises:
        EncryptionError: 복호화 실패 (잘못된 키, 변조된 데이터 등)

    Example:
        >>> encrypted = encrypt_password("my_password")
        >>> decrypted = decrypt_password(encrypted)
        >>> decrypted
        'my_password'
    """
    try:
        # 암호화 키 가져오기
        key = _get_encryption_key()

        # AES-GCM 암호화 객체 생성
        aesgcm = AESGCM(key)

        # nonce와 ciphertext 분리
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]

        # 복호화 수행
        # GCM 모드는 자동으로 인증 태그 검증
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode('utf-8')

    except Exception as e:
        raise EncryptionError(f"Failed to decrypt password: {str(e)}")


def verify_encryption_keys() -> bool:
    """
    암호화 키가 올바르게 설정되어 있는지 확인

    Returns:
        bool: 키가 올바르게 설정되어 있으면 True
    """
    try:
        _get_encryption_key()
        return True
    except EncryptionError:
        return False


# 테스트 함수 (개발 용도)
def _test_encryption():
    """암호화/복호화 라운드트립 테스트"""
    test_password = "test_password_1234!@#$"

    # 암호화
    encrypted = encrypt_password(test_password)
    print(f"Original: {test_password}")
    print(f"Encrypted (hex): {encrypted.hex()}")
    print(f"Encrypted length: {len(encrypted)} bytes")

    # 복호화
    decrypted = decrypt_password(encrypted)
    print(f"Decrypted: {decrypted}")

    # 검증
    assert test_password == decrypted, "Decryption failed!"
    print("✓ Encryption/Decryption test passed!")


if __name__ == "__main__":
    # 스크립트로 직접 실행 시 테스트
    _test_encryption()
