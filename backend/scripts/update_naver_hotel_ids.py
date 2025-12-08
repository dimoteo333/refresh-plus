"""
네이버 호텔 ID를 accommodations 테이블에 업데이트하는 스크립트
- backend/docs/naver_hotel_ids.csv를 읽어 DB에 naver_hotel_id 컬럼을 채웁니다.
- 반드시 DB에 naver_hotel_id 컬럼이 추가된 상태여야 합니다.
"""

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Dict, Tuple


def load_id_mapping(csv_path: Path) -> Dict[str, str]:
    """
    CSV에서 호텔명 → 네이버 호텔 ID 매핑을 생성합니다.
    """
    mapping: Dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("호텔명") or "").strip()
            naver_id = (row.get("네이버 호텔 ID") or "").strip()

            if not name or not naver_id:
                continue

            mapping[name] = naver_id
    return mapping


def ensure_column_exists(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA table_info(accommodations)")
    columns = {row[1] for row in cursor.fetchall()}
    if "naver_hotel_id" not in columns:
        raise SystemExit("naver_hotel_id column is missing. Run ALTER TABLE before executing this script.")


def ensure_index(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_accommodations_naver_hotel_id "
        "ON accommodations (naver_hotel_id)"
    )


def update_naver_ids(conn: sqlite3.Connection, mapping: Dict[str, str]) -> Tuple[int, int]:
    """
    DB에 네이버 호텔 ID를 업데이트하고, 업데이트된 건수와 매칭 실패 건수를 반환합니다.
    """
    updated = 0
    missing = 0

    for name, naver_id in mapping.items():
        cur = conn.execute(
            "UPDATE accommodations SET naver_hotel_id = ? WHERE name = ?",
            (naver_id, name),
        )
        if cur.rowcount:
            updated += cur.rowcount
        else:
            missing += 1

    conn.commit()
    return updated, missing


def main():
    parser = argparse.ArgumentParser(description="Populate accommodations.naver_hotel_id from CSV")
    parser.add_argument(
        "--db-path",
        default=Path(__file__).resolve().parents[1] / "refresh_plus.db",
        type=Path,
        help="Path to SQLite database (default: backend/refresh_plus.db)",
    )
    parser.add_argument(
        "--csv-path",
        default=Path(__file__).resolve().parents[1] / "docs" / "naver_hotel_ids.csv",
        type=Path,
        help="Path to CSV file with hotel IDs",
    )
    args = parser.parse_args()

    if not args.csv_path.exists():
        raise SystemExit(f"CSV file not found: {args.csv_path}")
    if not args.db_path.exists():
        raise SystemExit(f"DB file not found: {args.db_path}")

    mapping = load_id_mapping(args.csv_path)
    if not mapping:
        raise SystemExit("No valid rows found in CSV (check headers and data).")

    conn = sqlite3.connect(args.db_path)
    try:
        ensure_column_exists(conn)
        ensure_index(conn)
        updated, missing = update_naver_ids(conn, mapping)
    finally:
        conn.close()

    print(f"Updated rows: {updated}")
    print(f"Not matched (name not found): {missing}")
    print("Done.")


if __name__ == "__main__":
    main()
