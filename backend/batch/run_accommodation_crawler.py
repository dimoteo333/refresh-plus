#!/usr/bin/env python3
"""
Standalone script to run accommodation crawling batch job
Can be triggered by Railway Cron Jobs or external schedulers
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.batch.accommodation_crawler import process_accommodation_crawling
from app.config import settings

if __name__ == "__main__":
    print("Starting accommodation crawling batch job...")
    
    # 설정 확인
    if not settings.LULU_LALA_USERNAME or not settings.LULU_LALA_PASSWORD:
        print("ERROR: LULU_LALA_USERNAME and LULU_LALA_PASSWORD must be set in .env file")
        sys.exit(1)
    
    if not settings.LULU_LALA_RSA_PUBLIC_KEY:
        print("ERROR: LULU_LALA_RSA_PUBLIC_KEY must be set in .env file")
        sys.exit(1)
    
    result = asyncio.run(process_accommodation_crawling())
    print(f"Accommodation crawling completed: {result}")
    
    if result.get("status") == "error":
        sys.exit(1)
    else:
        sys.exit(0)

