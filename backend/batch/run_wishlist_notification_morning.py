#!/usr/bin/env python3
"""
위시리스트 알림 배치 작업 실행 스크립트 (오전 09:00 KST)
"""

import asyncio
import sys
import os
from pathlib import Path

# 부모 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.batch.wishlist_notification_morning import process_wishlist_notification_morning

if __name__ == "__main__":
    print("Starting wishlist notification batch job (morning)...")

    result = asyncio.run(process_wishlist_notification_morning())
    print(f"Wishlist notification (morning) completed: {result}")

    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)
