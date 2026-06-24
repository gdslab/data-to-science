"""Backfill file_size for existing data products and raw data.

Populates the on-disk byte size for active data products and raw data that were
created before the file_size column existed, so per-user data usage can be a
fast SQL SUM instead of a filesystem walk.

Usage:
    docker compose exec backend python app/utils/backfill_file_sizes.py
"""

import sys
from pathlib import Path

from sqlalchemy import select

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app import crud
from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.models.raw_data import RawData


def backfill_file_sizes():
    """Backfill file_size for active data products and raw data missing it."""
    db = SessionLocal()

    try:
        data_product_ids = (
            db.execute(
                select(DataProduct.id).where(
                    DataProduct.is_active == True,
                    DataProduct.file_size.is_(None),
                )
            )
            .scalars()
            .all()
        )
        raw_data_ids = (
            db.execute(
                select(RawData.id).where(
                    RawData.is_active == True,
                    RawData.file_size.is_(None),
                )
            )
            .scalars()
            .all()
        )

        print(
            f"Found {len(data_product_ids)} data products and "
            f"{len(raw_data_ids)} raw data records to process"
        )

        success_count = 0
        error_count = 0

        for data_product_id in data_product_ids:
            try:
                size = crud.data_product.set_file_size(db, data_product_id)
                success_count += 1
                print(f"✓ data product {data_product_id}: {size} bytes")
            except Exception as e:
                error_count += 1
                print(f"✗ data product {data_product_id}: {e}")

        for raw_data_id in raw_data_ids:
            try:
                size = crud.raw_data.set_file_size(db, raw_data_id)
                success_count += 1
                print(f"✓ raw data {raw_data_id}: {size} bytes")
            except Exception as e:
                error_count += 1
                print(f"✗ raw data {raw_data_id}: {e}")

        print("\nBackfill complete:")
        print(f"  Success: {success_count}")
        print(f"  Errors: {error_count}")

    finally:
        db.close()


if __name__ == "__main__":
    backfill_file_sizes()
