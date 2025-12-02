#!/usr/bin/env python3
"""
Standalone script to run score recovery batch job
Can be triggered by Railway Cron Jobs or external schedulers
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.batch.score_recovery import process_score_recovery

if __name__ == "__main__":
    print("Starting score recovery batch job...")
    result = asyncio.run(process_score_recovery())
    print(f"Score recovery completed: {result}")
    sys.exit(0)
