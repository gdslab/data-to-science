"""Generate GeoParquet files for existing vector layers.

This script generates GeoParquet files for vector layers that were created
before the GeoParquet feature was implemented. It can process all layers or
filter by project.

Usage:
    # Generate parquet for all vector layers
    docker compose exec backend python app/utils/generate_parquet_files.py

    # Generate parquet for a specific project
    docker compose exec backend python app/utils/generate_parquet_files.py --project-id <uuid>

    # Force regeneration even if parquet file exists
    docker compose exec backend python app/utils/generate_parquet_files.py --force

    # Generate synchronously (without Celery)
    docker compose exec backend python app/utils/generate_parquet_files.py --sync
"""

import argparse
import os
import sys
from pathlib import Path
from uuid import UUID

import geopandas as gpd
from sqlalchemy import select, distinct

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app import crud
from app.api.utils import save_vector_layer_parquet, get_static_dir
from app.db.session import SessionLocal
from app.models.vector_layer import VectorLayer


def generate_parquet_for_layer(
    db,
    project_id: UUID,
    layer_id: str,
    force: bool = False,
) -> tuple[bool, str]:
    """Generate parquet file for a single vector layer.

    Args:
        db: Database session
        project_id: Project UUID
        layer_id: Layer ID
        force: If True, regenerate even if file exists

    Returns:
        Tuple of (success: bool, message: str)
    """
    static_dir = get_static_dir()
    parquet_path = os.path.join(
        static_dir, "projects", str(project_id), "vector", layer_id, f"{layer_id}.parquet"
    )

    # Check if parquet file already exists
    if os.path.exists(parquet_path) and not force:
        return True, "skipped (already exists)"

    try:
        # Fetch features from database
        features = crud.vector_layer.get_vector_layer_by_id(
            db, project_id=project_id, layer_id=layer_id
        )

        if not features:
            return False, "no features found"

        # Convert features to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

        # Generate parquet file
        save_vector_layer_parquet(project_id, layer_id, gdf, static_dir)

        return True, "generated"

    except Exception as e:
        return False, f"error: {str(e)}"


def backfill_parquet(project_id: UUID = None, force: bool = False, sync: bool = True):
    """Backfill GeoParquet files for all vector layers.

    Args:
        project_id: Optional project UUID to filter layers
        force: If True, regenerate even if file exists
        sync: If True, generate synchronously. If False, use Celery tasks.
    """
    db = SessionLocal()

    try:
        # Build query for unique layer_id and project_id combinations
        query = select(
            distinct(VectorLayer.layer_id),
            VectorLayer.project_id,
            VectorLayer.layer_name,
        ).where(VectorLayer.is_active == True)

        # Filter by project if specified
        if project_id:
            query = query.where(VectorLayer.project_id == project_id)

        # Order for consistent output
        query = query.order_by(VectorLayer.project_id, VectorLayer.layer_id)

        results = db.execute(query).all()

        print(f"Found {len(results)} vector layers to process")
        if project_id:
            print(f"Filtering for project: {project_id}")
        if force:
            print("Force mode: regenerating existing parquet files")
        print()

        success_count = 0
        skip_count = 0
        error_count = 0

        for layer_id, proj_id, layer_name in results:
            success, message = generate_parquet_for_layer(
                db, proj_id, layer_id, force=force
            )

            if success:
                if message == "generated":
                    success_count += 1
                    print(f"✓ Generated {layer_id} ({layer_name}) in project {proj_id}")
                else:  # skipped
                    skip_count += 1
                    print(f"⊘ Skipped {layer_id} ({layer_name}) - {message}")
            else:
                error_count += 1
                print(f"✗ Failed {layer_id} ({layer_name}): {message}")

        print(f"\nBackfill complete:")
        print(f"  Generated: {success_count}")
        print(f"  Skipped: {skip_count}")
        print(f"  Errors: {error_count}")

    finally:
        db.close()


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate GeoParquet files for existing vector layers"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        help="Only process vector layers for a specific project UUID",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate parquet files even if they already exist",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Generate parquet files synchronously (default behavior)",
    )

    args = parser.parse_args()

    # Validate project_id if provided
    project_id = None
    if args.project_id:
        try:
            project_id = UUID(args.project_id)
        except ValueError:
            print(f"Error: Invalid project ID '{args.project_id}'. Must be a valid UUID.")
            sys.exit(1)

    # Run backfill
    backfill_parquet(project_id=project_id, force=args.force, sync=args.sync)


if __name__ == "__main__":
    main()
