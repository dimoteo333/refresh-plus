#!/usr/bin/env python3
"""FAQ 통계 확인 스크립트"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.faq import FAQ
from sqlalchemy import select, func

async def check_stats():
    async with AsyncSessionLocal() as db:
        # 카테고리별 개수
        result = await db.execute(
            select(FAQ.category, func.count(FAQ.id)).group_by(FAQ.category)
        )
        
        print("\n카테고리별 FAQ 개수:")
        print("=" * 60)
        total = 0
        for cat, cnt in result.all():
            print(f"{cat or '(카테고리 없음)':30} {cnt:3}개")
            total += cnt
        print("=" * 60)
        print(f"{'총계':30} {total:3}개\n")

if __name__ == "__main__":
    asyncio.run(check_stats())

