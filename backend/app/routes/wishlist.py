from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.wishlist import Wishlist
from app.models.accommodation import Accommodation
from app.schemas.wishlist import WishlistCreate, WishlistUpdate, WishlistResponse
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
        select(Wishlist).where(
            (Wishlist.user_id == current_user.id) &
            (Wishlist.is_active == True)
        )
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

    # 숙소 존재 확인
    accommodation_result = await db.execute(
        select(Accommodation).where(Accommodation.id == wishlist_data.accommodation_id)
    )
    accommodation = accommodation_result.scalar_one_or_none()

    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")

    # 이미 존재하는지 확인 (user_id + accommodation_id + desired_date 조합)
    existing = await db.execute(
        select(Wishlist).where(
            (Wishlist.user_id == current_user.id) &
            (Wishlist.accommodation_id == wishlist_data.accommodation_id) &
            (Wishlist.desired_date == wishlist_data.desired_date) &
            (Wishlist.is_active == True)
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in wishlist")

    # 최대 개수 확인
    count_result = await db.execute(
        select(func.count(Wishlist.id)).where(
            (Wishlist.user_id == current_user.id) &
            (Wishlist.is_active == True)
        )
    )
    count = count_result.scalar()

    if count >= settings.MAX_WISHLIST_ITEMS:
        raise HTTPException(status_code=400, detail="Wishlist is full")

    # 추가
    wishlist_item = Wishlist(
        id=f"wishlist_{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
        accommodation_id=wishlist_data.accommodation_id,
        desired_date=wishlist_data.desired_date,
        notify_enabled=wishlist_data.notify_enabled,
        notification_type=wishlist_data.notification_type,
        fcm_token=wishlist_data.fcm_token,
        is_active=True
    )

    db.add(wishlist_item)
    await db.commit()
    await db.refresh(wishlist_item)

    return wishlist_item

@router.patch("/{wishlist_id}", response_model=WishlistResponse)
async def update_wishlist(
    wishlist_id: str,
    wishlist_data: WishlistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """찜하기 수정"""

    result = await db.execute(
        select(Wishlist).where(
            (Wishlist.id == wishlist_id) &
            (Wishlist.user_id == current_user.id)
        )
    )
    wishlist_item = result.scalar_one_or_none()

    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    # 업데이트할 필드만 변경
    if wishlist_data.desired_date is not None:
        wishlist_item.desired_date = wishlist_data.desired_date
    if wishlist_data.notify_enabled is not None:
        wishlist_item.notify_enabled = wishlist_data.notify_enabled
    if wishlist_data.notification_type is not None:
        wishlist_item.notification_type = wishlist_data.notification_type
    if wishlist_data.fcm_token is not None:
        wishlist_item.fcm_token = wishlist_data.fcm_token

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

    # Soft delete
    wishlist_item.is_active = False

    await db.commit()

    return {"message": "Removed from wishlist"}

@router.delete("/accommodation/{accommodation_id}")
async def remove_from_wishlist_by_accommodation(
    accommodation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """숙소 ID로 찜하기 삭제 (모든 날짜 알림 포함)"""

    result = await db.execute(
        select(Wishlist).where(
            (Wishlist.user_id == current_user.id) &
            (Wishlist.accommodation_id == accommodation_id) &
            (Wishlist.is_active == True)
        )
    )
    wishlist_items = result.scalars().all()

    if not wishlist_items:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    # Soft delete - 모든 항목 삭제 (날짜별 알림 포함)
    deleted_count = 0
    for item in wishlist_items:
        item.is_active = False
        deleted_count += 1

    await db.commit()

    return {"message": f"Removed {deleted_count} item(s) from wishlist"}
