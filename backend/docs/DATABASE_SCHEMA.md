# 데이터베이스 스키마 문서

## 테이블 목록

### 1. accommodations (숙소 정보 원장)

**테이블명**: `accommodations`

**설명**: 숙소의 기본 정보를 저장하는 원장 테이블

**컬럼 목록**:

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | VARCHAR | PRIMARY KEY, INDEX | 숙소Id (PK) |
| `region` | VARCHAR | INDEX | 지역 |
| `accommodation_id` | VARCHAR | INDEX, NULLABLE | 숙소id (원본 시스템의 ID) |
| `name` | VARCHAR | INDEX | 숙소명 |
| `address` | TEXT | NULLABLE | 주소 |
| `contact` | VARCHAR | NULLABLE | 연락처 |
| `check_in_out` | VARCHAR | NULLABLE | 체크인/아웃 |
| `website` | VARCHAR | NULLABLE | 홈페이지 |
| `accommodation_type` | VARCHAR | NULLABLE | 숙소 타입 |
| `capacity` | INTEGER | DEFAULT 2 | 숙소 인원 |
| `images` | JSON | DEFAULT [] | 숙소 이미지 URL (여러 개) |
| `summary` | JSON | DEFAULT [] | 숙소 특징 요약 (최대 5개) |
| `created_at` | DATETIME | DEFAULT NOW() | 등록시간 |
| `updated_at` | DATETIME | DEFAULT NOW() | 업데이트시간 |

**인덱스**:
- `ix_accommodations_id` (id)
- `ix_accommodations_region` (region)
- `ix_accommodations_accommodation_id` (accommodation_id)
- `ix_accommodations_name` (name)

---

### 2. accommodation_dates (날짜별 숙소 내역)

**테이블명**: `accommodation_dates`

**설명**: 각 숙소의 날짜별 예약 정보를 저장하는 테이블

**컬럼 목록**:

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | VARCHAR | PRIMARY KEY, INDEX | Primary Key |
| `year` | INTEGER | INDEX | 연도 |
| `week_number` | INTEGER | NULLABLE | 몇주차 |
| `month` | INTEGER | INDEX | 월 |
| `day` | INTEGER | INDEX | 일 |
| `weekday` | INTEGER | NULLABLE | 요일 (0=월요일, 6=일요일) |
| `date` | VARCHAR | INDEX | 날짜 (YYYY-MM-DD 형식) |
| `accommodation_id` | VARCHAR | FK → accommodations.id, INDEX | 숙소id |
| `applicants` | INTEGER | DEFAULT 0 | 신청인원 |
| `score` | FLOAT | DEFAULT 0.0 | 점수 |
| `status` | VARCHAR | INDEX, NULLABLE | 신청상태 (예: "신청중", "마감", "신청불가", "객실없음" 등) |
| `created_at` | DATETIME | DEFAULT NOW() | 등록시간 |
| `updated_at` | DATETIME | DEFAULT NOW() | 업데이트시간 |

**인덱스**:
- `ix_accommodation_dates_id` (id)
- `ix_accommodation_dates_year` (year)
- `ix_accommodation_dates_month` (month)
- `ix_accommodation_dates_day` (day)
- `ix_accommodation_dates_date` (date)
- `ix_accommodation_dates_status` (status)
- `ix_accommodation_dates_accommodation_id` (accommodation_id)

**외래키**:
- `accommodation_id` → `accommodations.id`

---

### 3. users (사용자 정보)

**테이블명**: `users`

**설명**: 사용자의 기본 정보를 저장하는 테이블

**컬럼 목록**:

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | VARCHAR | PRIMARY KEY, INDEX | 사용자id (PK) |
| `name` | VARCHAR | | 사용자명 |
| `points` | FLOAT | DEFAULT 100 | 점수 (소수점 지원) |
| `available_nights` | INTEGER | DEFAULT 0 | 사용가능박수 |
| `created_at` | DATETIME | DEFAULT NOW() | 등록시간 |
| `updated_at` | DATETIME | DEFAULT NOW() | 업데이트시간 |

**인덱스**:
- `ix_users_id` (id)

---

### 4. wishlists (사용자별 즐겨찾기 목록)

**테이블명**: `wishlists`

**설명**: 사용자가 즐겨찾기한 숙소 목록을 저장하는 테이블

**컬럼 목록**:

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | VARCHAR | PRIMARY KEY, INDEX | Primary Key |
| `user_id` | VARCHAR | FK → users.id, INDEX | 사용자id |
| `accommodation_id` | VARCHAR | FK → accommodations.id, INDEX | 숙소id |
| `is_active` | BOOLEAN | DEFAULT TRUE | 등록여부 |
| `notify_enabled` | BOOLEAN | DEFAULT TRUE | 알림여부 |
| `created_at` | DATETIME | DEFAULT NOW() | 등록시간 |
| `updated_at` | DATETIME | DEFAULT NOW() | 업데이트시간 |

**인덱스**:
- `ix_wishlists_id` (id)
- `ix_wishlists_user_id` (user_id)
- `ix_wishlists_accommodation_id` (accommodation_id)

**외래키**:
- `user_id` → `users.id`
- `accommodation_id` → `accommodations.id`

---

### 5. today_accommodation_info (오늘자 숙소 내역)

**테이블명**: `today_accommodation_info`

**설명**: 오늘 날짜의 숙소 예약 정보를 실시간으로 관리하는 테이블 (실시간 성이 필요해 별도 관리)

**컬럼 목록**:

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | VARCHAR | PRIMARY KEY, INDEX | Primary Key |
| `year` | INTEGER | INDEX | 연도 |
| `week_number` | INTEGER | NULLABLE | 몇주차 |
| `month` | INTEGER | INDEX | 월 |
| `day` | INTEGER | INDEX | 일 |
| `weekday` | INTEGER | NULLABLE | 요일 (0=월요일, 6=일요일) |
| `date` | VARCHAR | INDEX | 날짜 (YYYY-MM-DD 형식) |
| `accommodation_id` | VARCHAR | FK → accommodations.id, INDEX | 숙소id |
| `applicants` | INTEGER | DEFAULT 0 | 신청인원 |
| `score` | FLOAT | DEFAULT 0.0 | 점수 |
| `status` | VARCHAR | INDEX, NULLABLE | 신청상태 (예: "신청중", "마감", "신청불가", "객실없음" 등) |
| `created_at` | DATETIME | DEFAULT NOW() | 등록시간 |
| `updated_at` | DATETIME | DEFAULT NOW() | 업데이트시간 |

**인덱스**:
- `ix_today_accommodation_info_id` (id)
- `ix_today_accommodation_info_year` (year)
- `ix_today_accommodation_info_month` (month)
- `ix_today_accommodation_info_day` (day)
- `ix_today_accommodation_info_date` (date)
- `ix_today_accommodation_info_status` (status)
- `ix_today_accommodation_info_accommodation_id` (accommodation_id)

**외래키**:
- `accommodation_id` → `accommodations.id`

**참고**: 이 테이블은 실시간 성능을 위해 별도로 관리되며, 오늘 날짜의 데이터만 저장합니다. 매일 자정에 정리되거나 `accommodation_dates`로 이관될 수 있습니다.

---

## 테이블 관계도

```
accommodations (1) ──< (N) accommodation_dates
accommodations (1) ──< (N) today_accommodation_info
accommodations (1) ──< (N) wishlists
users (1) ──< (N) wishlists
```

---

## 주요 변경사항

### 이전 스키마에서 변경된 점:

1. **accommodations 테이블**:
   - `date_booking_info` (JSON) 제거 → 별도 테이블(`accommodation_dates`)로 분리
   - `price`, `rating`, `amenities`, `available_rooms` 제거
   - `address`, `contact`, `check_in_out`, `website`, `accommodation_type` 추가
   - `accommodation_id` 추가 (원본 시스템 ID)

2. **새로운 테이블 추가**:
   - `accommodation_dates`: 날짜별 숙소 내역
   - `today_accommodation_info`: 오늘자 숙소 내역 (실시간 성능)

3. **users 테이블 간소화**:
   - `email`, `current_points`, `max_points`, `total_bookings`, `successful_bookings`, `firebase_token`, `kakao_user_id`, `last_point_recovery`, `tier` 제거
   - `points`, `available_nights`로 간소화

4. **wishlists 테이블**:
   - `notify_when_bookable` → `notify_enabled`로 변경
   - `is_active` 추가 (등록여부)
   - `updated_at` 추가

5. **bookings 테이블 제거**:
   - 요청된 스키마에 없으므로 제거됨 (필요시 별도로 추가 가능)

---

## 데이터베이스 재생성 방법

```bash
cd backend
python scripts/recreate_database.py
```
