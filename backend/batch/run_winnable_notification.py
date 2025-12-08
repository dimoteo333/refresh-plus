#!/usr/bin/env python3
"""
당첨 가능성 높음 알림 배치 작업 실행 스크립트 (12:00 KST)
"""

import asyncio
import sys
import os
from pathlib import Path

# 부모 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.batch.winnable_notification import process_winnable_notification

if __name__ == "__main__":
    print("Starting winnable notification batch job...")

    result = asyncio.run(process_winnable_notification())
    print(f"Winnable notification completed: {result}")

    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)
