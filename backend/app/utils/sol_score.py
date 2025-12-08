"""
SOL점수 계산 유틸리티

SOL점수는 숙소의 온라인 최저가 대비 신청 점수의 효율성을 나타내는 지표입니다.
- 계산 방식: (온라인 최저가) / (가중치 적용된 신청 점수)
- 신청 점수 가중치:
  * 90점 이상: 0.7배 (높은 점수 → 낮은 가중치)
  * 70~90점: 1.0배 (중간 가치)
  * 70점 이하: 1.3배 (낮은 점수 → 높은 가중치)
- 정규화: 모든 데이터의 효율성 값을 0~100점으로 Min-Max 정규화
- 온라인 최저가 또는 신청 점수가 없는 경우 계산 대상에서 제외
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func as sql_func
from app.models.accommodation_date import AccommodationDate
from app.models.today_accommodation import TodayAccommodation
from app.models.accommodation import Accommodation


def get_score_weight(score: float) -> float:
    """
    신청 점수에 따른 가중치를 반환합니다.

    높은 점수에는 낮은 가중치, 낮은 점수에는 높은 가중치를 적용하여
    높은 점수를 요구하는 숙소의 효율성(SOL점수)이 높아집니다.

    Args:
        score: 신청 점수 (0~100)

    Returns:
        가중치 (0.7 ~ 1.3)
    """
    if score >= 90:
        return 0.7  # 높은 점수 → 낮은 가중치
    elif score >= 70:
        return 1.0  # 중간 가치
    else:
        return 1.3  # 낮은 점수 → 높은 가중치


async def calculate_and_update_sol_scores(
    db: AsyncSession,
    model_class: type[AccommodationDate | TodayAccommodation]
) -> Dict[str, int]:
    """
    지정된 모델의 모든 레코드에 대해 SOL점수를 계산하고 업데이트합니다.

    Args:
        db: 데이터베이스 세션
        model_class: AccommodationDate 또는 TodayAccommodation 모델 클래스

    Returns:
        업데이트 통계 딕셔너리
        {
            'total': 전체 레코드 수,
            'calculated': SOL점수가 계산된 레코드 수,
            'skipped': 계산 대상에서 제외된 레코드 수
        }
    """
    # 1. 모든 레코드 조회
    result = await db.execute(select(model_class))
    all_records = result.scalars().all()

    total_count = len(all_records)

    # 2. 유효한 데이터 필터링 및 효율성 계산
    valid_records = []
    efficiencies = []

    for record in all_records:
        # online_price와 score가 모두 존재하고 score가 0보다 큰 경우만 계산
        if (record.online_price is not None and
            record.score is not None and
            record.score > 0):
            # 신청 점수에 가중치 적용
            weight = get_score_weight(record.score)
            weighted_score = record.score * weight

            # 효율성 = 온라인 최저가 / 가중치 적용된 신청 점수
            efficiency = record.online_price / weighted_score
            valid_records.append(record)
            efficiencies.append(efficiency)

    calculated_count = len(valid_records)
    skipped_count = total_count - calculated_count

    # 3. 유효한 데이터가 없는 경우
    if calculated_count == 0:
        return {
            'total': total_count,
            'calculated': 0,
            'skipped': skipped_count
        }

    # 4. Min-Max 정규화
    min_efficiency = min(efficiencies)
    max_efficiency = max(efficiencies)

    # 모든 효율성 값이 동일한 경우 (max == min)
    if max_efficiency == min_efficiency:
        # 모든 레코드에 50점 부여 (중간값)
        for record in valid_records:
            record.sol_score = 50.0
    else:
        # 정규화: (value - min) / (max - min) * 100
        for i, record in enumerate(valid_records):
            normalized_score = ((efficiencies[i] - min_efficiency) /
                              (max_efficiency - min_efficiency)) * 100
            record.sol_score = round(normalized_score, 2)

    # 5. 유효하지 않은 레코드는 sol_score를 None으로 설정
    for record in all_records:
        if record not in valid_records:
            record.sol_score = None

    # 6. 변경사항 커밋
    await db.commit()

    return {
        'total': total_count,
        'calculated': calculated_count,
        'skipped': skipped_count
    }


async def calculate_sol_scores_for_accommodation_dates(db: AsyncSession) -> Dict[str, int]:
    """
    accommodation_dates 테이블의 모든 레코드에 대해 SOL점수를 계산하고 업데이트합니다.

    Args:
        db: 데이터베이스 세션

    Returns:
        업데이트 통계 딕셔너리
    """
    return await calculate_and_update_sol_scores(db, AccommodationDate)


async def calculate_sol_scores_for_today_accommodation(db: AsyncSession) -> Dict[str, int]:
    """
    today_accommodation_info 테이블의 모든 레코드에 대해 SOL점수를 계산하고 업데이트합니다.

    Args:
        db: 데이터베이스 세션

    Returns:
        업데이트 통계 딕셔너리
    """
    return await calculate_and_update_sol_scores(db, TodayAccommodation)


async def get_top_sol_score_dates(
    db: AsyncSession,
    limit: int = 10,
    exclude_unavailable: bool = True
) -> List[AccommodationDate]:
    """
    SOL점수가 높은 날짜 목록을 반환합니다.

    Args:
        db: 데이터베이스 세션
        limit: 반환할 최대 레코드 수
        exclude_unavailable: True인 경우 신청 불가능한 날짜 제외

    Returns:
        SOL점수가 높은 순으로 정렬된 AccommodationDate 리스트
    """
    query = select(AccommodationDate).where(
        AccommodationDate.sol_score.isnot(None)
    )

    if exclude_unavailable:
        query = query.where(
            and_(
                AccommodationDate.status.notin_(['마감', '신청불가', '객실없음']),
                AccommodationDate.status.isnot(None)
            )
        )

    query = query.order_by(AccommodationDate.sol_score.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def calculate_and_update_average_sol_scores(db: AsyncSession) -> Dict[str, int]:
    """
    각 숙소의 평균 SOL점수를 계산하고 accommodations 테이블에 업데이트합니다.

    각 숙소에 대해 accommodation_dates의 모든 SOL점수를 평균하여 저장합니다.
    SOL점수가 없는 날짜는 제외됩니다.

    Args:
        db: 데이터베이스 세션

    Returns:
        업데이트 통계 딕셔너리
        {
            'total': 전체 숙소 수,
            'updated': 평균 SOL점수가 계산된 숙소 수,
            'skipped': 계산 대상에서 제외된 숙소 수
        }
    """
    # 1. 모든 숙소 조회
    result = await db.execute(select(Accommodation))
    all_accommodations = result.scalars().all()

    total_count = len(all_accommodations)
    updated_count = 0
    skipped_count = 0

    # 2. 각 숙소별로 평균 SOL점수 계산
    for accommodation in all_accommodations:
        # 해당 숙소의 모든 날짜별 SOL점수 조회
        dates_result = await db.execute(
            select(AccommodationDate)
            .where(
                and_(
                    AccommodationDate.accommodation_id == accommodation.id,
                    AccommodationDate.sol_score.isnot(None)
                )
            )
        )
        dates = dates_result.scalars().all()

        # SOL점수가 있는 날짜가 없으면 스킵
        if not dates:
            accommodation.average_sol_score = None
            skipped_count += 1
            continue

        # 평균 SOL점수 계산
        sol_scores = [date.sol_score for date in dates]
        average_sol_score = sum(sol_scores) / len(sol_scores)

        # 소수점 둘째 자리까지 반올림
        accommodation.average_sol_score = round(average_sol_score, 2)
        updated_count += 1

    # 3. 변경사항 커밋
    await db.commit()

    return {
        'total': total_count,
        'updated': updated_count,
        'skipped': skipped_count
    }


async def get_top_accommodations_by_sol_score(
    db: AsyncSession,
    limit: int = 10,
    min_sol_score: Optional[float] = None
) -> List[Accommodation]:
    """
    평균 SOL점수가 높은 숙소 목록을 반환합니다.

    Args:
        db: 데이터베이스 세션
        limit: 반환할 최대 숙소 수
        min_sol_score: 최소 SOL점수 (이 점수 이상만 조회)

    Returns:
        평균 SOL점수가 높은 순으로 정렬된 Accommodation 리스트
    """
    query = select(Accommodation).where(
        Accommodation.average_sol_score.isnot(None)
    )

    if min_sol_score is not None:
        query = query.where(Accommodation.average_sol_score >= min_sol_score)

    query = query.order_by(Accommodation.average_sol_score.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
