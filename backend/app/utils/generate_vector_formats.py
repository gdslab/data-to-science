"""Generate GeoParquet and FlatGeobuf files for existing vector layers.

This script generates vector format files (GeoParquet, FlatGeobuf) for vector layers
that were created before these features were implemented. It can process all layers or
filter by project, and allows selecting which formats to generate.

Usage:
    # Generate all formats for all vector layers
    docker compose exec backend python app/utils/generate_vector_formats.py

    # Generate only GeoParquet for all layers
    docker compose exec backend python app/utils/generate_vector_formats.py --format parquet

    # Generate only FlatGeobuf for all layers
    docker compose exec backend python app/utils/generate_vector_formats.py --format flatgeobuf

    # Generate for a specific project
    docker compose exec backend python app/utils/generate_vector_formats.py --project-id <uuid>

    # Force regeneration even if files exist
    docker compose exec backend python app/utils/generate_vector_formats.py --force

    # Generate synchronously (without Celery)
    docker compose exec backend python app/utils/generate_vector_formats.py --sync
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
from app.api.utils import (
    save_vector_layer_parquet,
    save_vector_layer_flatgeobuf,
    get_static_dir,
)
from app.db.session import SessionLocal
from app.models.vector_layer import VectorLayer


def generate_formats_for_layer(
    db,
    project_id: UUID,
    layer_id: str,
    formats: list[str],
    force: bool = False,
) -> dict[str, tuple[bool, str]]:
    """Generate format files for a single vector layer.

    Args:
        db: Database session
        project_id: Project UUID
        layer_id: Layer ID
        formats: List of formats to generate ("parquet", "flatgeobuf")
        force: If True, regenerate even if file exists

    Returns:
        Dict mapping format name to (success: bool, message: str)
    """
    static_dir = get_static_dir()
    results = {}

    # Fetch features from database once (shared by all formats)
    try:
        features = crud.vector_layer.get_vector_layer_by_id(
            db, project_id=project_id, layer_id=layer_id
        )

        if not features:
            for fmt in formats:
                results[fmt] = (False, "no features found")
            return results

        # Convert features to GeoDataFrame (shared by all formats)
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

    except Exception as e:
        for fmt in formats:
            results[fmt] = (False, f"error fetching data: {str(e)}")
        return results

    # Generate each requested format
    if "parquet" in formats:
        parquet_path = os.path.join(
            static_dir,
            "projects",
            str(project_id),
            "vector",
            layer_id,
            f"{layer_id}.parquet",
        )

        # Check if parquet file already exists
        if os.path.exists(parquet_path) and not force:
            results["parquet"] = (True, "skipped (already exists)")
        else:
            try:
                save_vector_layer_parquet(project_id, layer_id, gdf, static_dir)
                results["parquet"] = (True, "generated")
            except Exception as e:
                results["parquet"] = (False, f"error: {str(e)}")

    if "flatgeobuf" in formats:
        fgb_path = os.path.join(
            static_dir, "projects", str(project_id), "vector", layer_id, f"{layer_id}.fgb"
        )

        # Check if FlatGeobuf file already exists
        if os.path.exists(fgb_path) and not force:
            results["flatgeobuf"] = (True, "skipped (already exists)")
        else:
            try:
                save_vector_layer_flatgeobuf(project_id, layer_id, gdf, static_dir)
                results["flatgeobuf"] = (True, "generated")
            except Exception as e:
                results["flatgeobuf"] = (False, f"error: {str(e)}")

    return results


def backfill_formats(
    project_id: UUID = None,
    formats: list[str] = None,
    force: bool = False,
    sync: bool = True,
):
    """Backfill vector format files for all vector layers.

    Args:
        project_id: Optional project UUID to filter layers
        formats: List of formats to generate (default: ["parquet", "flatgeobuf"])
        force: If True, regenerate even if files exist
        sync: If True, generate synchronously. If False, use Celery tasks.
    """
    if formats is None:
        formats = ["parquet", "flatgeobuf"]

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
        print(f"Formats: {', '.join(formats)}")
        if force:
            print("Force mode: regenerating existing files")
        print()

        # Track counts per format
        format_stats = {fmt: {"generated": 0, "skipped": 0, "errors": 0} for fmt in formats}

        for layer_id, proj_id, layer_name in results:
            format_results = generate_formats_for_layer(
                db, proj_id, layer_id, formats=formats, force=force
            )

            # Build output line
            status_parts = []
            for fmt in formats:
                if fmt in format_results:
                    success, message = format_results[fmt]
                    if success:
                        if message == "generated":
                            format_stats[fmt]["generated"] += 1
                            status_parts.append(f"{fmt}:✓")
                        else:  # skipped
                            format_stats[fmt]["skipped"] += 1
                            status_parts.append(f"{fmt}:⊘")
                    else:
                        format_stats[fmt]["errors"] += 1
                        status_parts.append(f"{fmt}:✗")

            status_str = " ".join(status_parts)
            print(f"[{status_str}] {layer_id} ({layer_name}) in project {proj_id}")

        print(f"\nBackfill complete:")
        for fmt in formats:
            print(f"  {fmt.capitalize()}:")
            print(f"    Generated: {format_stats[fmt]['generated']}")
            print(f"    Skipped: {format_stats[fmt]['skipped']}")
            print(f"    Errors: {format_stats[fmt]['errors']}")

    finally:
        db.close()


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate vector format files (GeoParquet, FlatGeobuf) for existing vector layers"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        help="Only process vector layers for a specific project UUID",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["parquet", "flatgeobuf", "all"],
        default="all",
        help="Format to generate: parquet, flatgeobuf, or all (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate files even if they already exist",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Generate files synchronously (default behavior)",
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

    # Determine formats to generate
    if args.format == "all":
        formats = ["parquet", "flatgeobuf"]
    else:
        formats = [args.format]

    # Run backfill
    backfill_formats(project_id=project_id, formats=formats, force=args.force, sync=args.sync)


if __name__ == "__main__":
    main()
