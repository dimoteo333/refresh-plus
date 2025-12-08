#!/usr/bin/env python3
"""
위시리스트 알림 배치 작업 실행 스크립트 (저녁 20:00 KST)
"""

import asyncio
import sys
import os
from pathlib import Path

# 부모 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.batch.wishlist_notification_evening import process_wishlist_notification_evening

if __name__ == "__main__":
    print("Starting wishlist notification batch job (evening)...")

    result = asyncio.run(process_wishlist_notification_evening())
    print(f"Wishlist notification (evening) completed: {result}")

    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)
