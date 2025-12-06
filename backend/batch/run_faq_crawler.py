#!/usr/bin/env python3
"""
Standalone script to run FAQ crawling batch job (one-time)
Can be triggered manually or by external schedulers
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.batch.faq_crawler import process_faq_crawling
from app.config import settings

if __name__ == "__main__":
    print("Starting FAQ crawling batch job...")
    
    # 설정 확인
    if not settings.LULU_LALA_USERNAME or not settings.LULU_LALA_PASSWORD:
        print("ERROR: LULU_LALA_USERNAME and LULU_LALA_PASSWORD must be set in .env file")
        sys.exit(1)
    
    if not settings.LULU_LALA_RSA_PUBLIC_KEY:
        print("ERROR: LULU_LALA_RSA_PUBLIC_KEY must be set in .env file")
        sys.exit(1)
    
    result = asyncio.run(process_faq_crawling())
    print(f"FAQ crawling completed: {result}")
    
    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)

