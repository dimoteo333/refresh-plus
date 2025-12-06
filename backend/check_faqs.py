#!/usr/bin/env python3
"""FAQ 데이터 확인 스크립트"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.faq import FAQ
from sqlalchemy import select

async def check_faqs():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(FAQ))
        faqs = result.scalars().all()
        
        print(f"\n총 FAQ 개수: {len(faqs)}\n")
        print("=" * 60)
        
        for i, faq in enumerate(faqs, 1):
            print(f"\n{i}. 질문: {faq.question}")
            print(f"   답변: {faq.answer}")
            if faq.category:
                print(f"   카테고리: {faq.category}")
            print(f"   순서: {faq.order}")
            print("-" * 60)

if __name__ == "__main__":
    asyncio.run(check_faqs())

