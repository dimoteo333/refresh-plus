#!/usr/bin/env python3
"""
Standalone script to run daily ticketing batch job
Can be triggered by Railway Cron Jobs or external schedulers
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.batch.daily_ticketing import process_daily_ticketing

if __name__ == "__main__":
    print("Starting daily ticketing batch job...")
    result = asyncio.run(process_daily_ticketing())
    print(f"Daily ticketing completed: {result}")
    sys.exit(0)
