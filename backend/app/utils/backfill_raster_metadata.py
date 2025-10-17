"""Backfill bbox, crs, and resolution for existing data products.

This script calculates and stores spatial metadata for raster data products
that were created before the caching feature was implemented.

Usage:
    docker compose exec backend python app/utils/backfill_raster_metadata.py
"""

import sys
from pathlib import Path

from sqlalchemy import select

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.crud.crud_data_product import calculate_raster_metadata
from app.db.session import SessionLocal
from app.models.constants import NON_RASTER_TYPES
from app.models.data_product import DataProduct


def backfill_metadata():
    """Backfill raster metadata for all existing data products."""
    db = SessionLocal()

    try:
        # Get all raster data products without cached metadata
        query = (
            select(DataProduct)
            .where(
                DataProduct.is_active == True,
                DataProduct.bbox.is_(None),
            )
        )

        data_products = db.execute(query).scalars().all()

        # Filter out non-raster types
        raster_products = [
            dp for dp in data_products
            if dp.data_type not in NON_RASTER_TYPES
        ]

        print(f"Found {len(raster_products)} raster data products to process")

        success_count = 0
        skip_count = 0
        error_count = 0

        for dp in raster_products:
            try:
                metadata = calculate_raster_metadata(dp.filepath)
                if metadata:
                    dp.bbox = metadata["bbox"]
                    dp.crs = metadata["crs"]
                    dp.resolution = metadata["resolution"]
                    db.commit()
                    success_count += 1
                    print(f"✓ Updated {dp.id} ({dp.data_type})")
                else:
                    skip_count += 1
                    print(f"⊘ Skipped {dp.id} (not a valid raster or file not found)")
            except Exception as e:
                error_count += 1
                print(f"✗ Failed {dp.id}: {e}")
                db.rollback()

        print(f"\nBackfill complete:")
        print(f"  Success: {success_count}")
        print(f"  Skipped: {skip_count}")
        print(f"  Errors: {error_count}")

    finally:
        db.close()


if __name__ == "__main__":
    backfill_metadata()
