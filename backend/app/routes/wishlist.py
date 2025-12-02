from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.wishlist import Wishlist
from app.schemas.wishlist import WishlistCreate, WishlistResponse
from app.dependencies import get_current_user
from app.config import settings
from typing import List
import uuid

router = APIRouter()

@router.get("", response_model=List[WishlistResponse])
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """찜하기 목록 조회"""

    result = await db.execute(
        select(Wishlist).where(Wishlist.user_id == current_user.id)
    )
    wishlist_items = result.scalars().all()

    return wishlist_items

@router.post("", response_model=WishlistResponse)
async def add_to_wishlist(
    wishlist_data: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """찜하기 추가"""

    # 이미 존재하는지 확인
    existing = await db.execute(
        select(Wishlist).where(
            (Wishlist.user_id == current_user.id) &
            (Wishlist.accommodation_id == wishlist_data.accommodation_id)
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in wishlist")

    # 최대 개수 확인
    count_result = await db.execute(
        select(func.count(Wishlist.id)).where(Wishlist.user_id == current_user.id)
    )
    count = count_result.scalar()

    if count >= settings.MAX_WISHLIST_ITEMS:
        raise HTTPException(status_code=400, detail="Wishlist is full")

    # 추가
    wishlist_item = Wishlist(
        id=f"wishlist_{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        accommodation_id=wishlist_data.accommodation_id,
        notify_when_bookable=wishlist_data.notify_when_bookable
    )

    db.add(wishlist_item)
    await db.commit()
    await db.refresh(wishlist_item)

    return wishlist_item

@router.delete("/{wishlist_id}")
async def remove_from_wishlist(
    wishlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """찜하기 삭제"""

    result = await db.execute(
        select(Wishlist).where(
            (Wishlist.id == wishlist_id) &
            (Wishlist.user_id == current_user.id)
        )
    )
    wishlist_item = result.scalar_one_or_none()

    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    await db.delete(wishlist_item)
    await db.commit()

    return {"message": "Removed from wishlist"}
