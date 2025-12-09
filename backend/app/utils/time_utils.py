"""
시간 관련 유틸리티 함수

예약 가능 시간 체크 및 경고 메시지 생성
"""

from datetime import datetime
import pytz


def is_reservation_time_allowed() -> bool:
    """
    예약 가능 시간 체크 (08:00-21:00 KST)

    Returns:
        bool: 예약 가능 시간이면 True, 아니면 False
    """
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    hour = now.hour
    return 8 <= hour < 21


def get_time_warning_message() -> str | None:
    """
    20시 이후 경고 메시지 또는 예약 불가 시간 안내

    Returns:
        str | None: 경고 메시지 또는 None
    """
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    hour = now.hour

    if hour >= 20 and hour < 21:
        return "예약 가능 시간이 얼마 남지 않았습니다."
    elif hour < 8 or hour >= 21:
        return "예약은 08시~21시 사이에만 가능합니다."

    return None
