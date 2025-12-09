"""
전화번호 관련 유틸리티 함수

전화번호 파싱 및 검증
"""

import re


def parse_phone_number(phone: str) -> tuple[str, str, str]:
    """
    전화번호 파싱: 010-1234-5678 → ('010', '1234', '5678')

    Args:
        phone: 전화번호 문자열 (010-1234-5678 형식)

    Returns:
        tuple[str, str, str]: (앞 3자리, 가운데 4자리, 마지막 4자리)

    Raises:
        ValueError: 올바른 전화번호 형식이 아닐 경우
    """
    # 숫자만 추출
    digits = re.sub(r'\D', '', phone)

    if len(digits) != 11 or not digits.startswith('010'):
        raise ValueError("올바른 전화번호 형식이 아닙니다. (010-XXXX-XXXX)")

    return digits[:3], digits[3:7], digits[7:11]
