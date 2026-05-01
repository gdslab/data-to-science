"""Backfill S3 uploads for already-published STAC projects.

Uploads data product and raw data files to S3, updates s3_url in the database,
re-generates STAC items with S3 URLs, and re-publishes to the STAC API.

Usage:
    # Backfill all published projects
    docker compose exec backend python app/utils/backfill_s3_stac.py

    # Backfill a single project
    docker compose exec backend python app/utils/backfill_s3_stac.py --project-id <uuid>

    # Dry run (show what would be uploaded, no actual changes)
    docker compose exec backend python app/utils/backfill_s3_stac.py --dry-run
"""

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app import crud
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.data_product import DataProduct
from app.models.flight import Flight
from app.models.project import Project
from app.models.raw_data import RawData
from app.tasks.stac_tasks import (
    UUIDEncoder,
    _upload_to_s3_and_rewrite_hrefs,
    get_stac_cache_path,
)
from app.utils.s3 import is_s3_configured
from app.utils.stac.CachedSTACMetadata import CachedSTACMetadata
from app.utils.stac.STACCollectionManager import STACCollectionManager
from app.utils.stac.STACGenerator import STACGenerator


def get_cached_raw_data_link_ids(project_id: UUID) -> list:
    """Read the STAC cache file to detect which items had raw data links."""
    cache_path = get_stac_cache_path(project_id)
    if not cache_path.exists():
        return []

    try:
        with open(cache_path, "r") as f:
            cached_data = json.load(f)
        cache = CachedSTACMetadata(cached_data)
        return cache.get_raw_data_link_ids()
    except Exception:
        return []


def backfill_project(db, project: Project, dry_run: bool = False) -> bool:
    """Backfill S3 uploads for a single published project.

    Returns True on success, False on failure.
    """
    project_id = project.id
    print(f"\nProcessing project {project_id} ({project.title})...")

    # Check how many data products need uploading
    query = (
        select(DataProduct)
        .where(
            DataProduct.flight_id.in_(
                select(Flight.id).where(Flight.project_id == project_id)
            ),
            DataProduct.is_active == True,
            DataProduct.s3_url.is_(None),
        )
    )
    pending_dps = db.execute(query).scalars().all()

    query_done = (
        select(DataProduct)
        .where(
            DataProduct.flight_id.in_(
                select(Flight.id).where(Flight.project_id == project_id)
            ),
            DataProduct.is_active == True,
            DataProduct.s3_url.isnot(None),
        )
    )
    done_dps = db.execute(query_done).scalars().all()

    print(f"  Data products: {len(pending_dps)} to upload, {len(done_dps)} already in S3")

    # Detect raw data links from cache
    include_raw_data_links = get_cached_raw_data_link_ids(project_id)
    if include_raw_data_links:
        print(f"  Raw data links detected for {len(include_raw_data_links)} items")

    if dry_run:
        for dp in pending_dps:
            print(f"    [dry-run] Would upload: {dp.filepath}")
        return True

    # Load cached STAC metadata for re-generation
    cached_stac_metadata = None
    cache_path = get_stac_cache_path(project_id)
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cached_stac_metadata = json.load(f)
        except Exception:
            print("  Warning: Could not read cached STAC metadata")

    # Re-generate STAC items (with local URLs initially)
    sg = STACGenerator(
        db,
        project_id=project_id,
        cached_stac_metadata=cached_stac_metadata,
        include_raw_data_links=include_raw_data_links,
    )
    collection = sg.collection
    items = sg.items
    failed_items = sg.failed_items

    if not items:
        print("  No valid STAC items generated, skipping")
        return True

    print(f"  Generated {len(items)} STAC items ({len(failed_items)} failed)")

    # Upload to S3 and rewrite hrefs (skips files where s3_url is already set)
    uploaded_keys = _upload_to_s3_and_rewrite_hrefs(
        db, items, sg.flights, include_raw_data_links,
    )
    print(f"  Uploaded {len(uploaded_keys)} files to S3")

    # Re-publish to STAC API (PUT updates existing items)
    scm = STACCollectionManager(
        collection_id=str(project_id), collection=collection, items=items
    )
    report = scm.publish_to_catalog()

    published_count = sum(1 for item in report.items if item.is_published)
    failed_count = sum(1 for item in report.items if not item.is_published)
    print(f"  STAC API: {published_count} published, {failed_count} failed")

    # Update the local STAC cache
    try:
        items_dicts = [item.to_dict() for item in items]
        response_data = {
            "collection_id": str(project_id),
            "collection": collection.to_dict(),
            "items": items_dicts,
            "is_published": True,
        }
        if failed_items:
            response_data["failed_items"] = [
                item.model_dump() for item in failed_items
            ]
        with open(cache_path, "w") as f:
            json.dump(response_data, f, indent=2, cls=UUIDEncoder)
    except Exception as e:
        print(f"  Warning: Could not update STAC cache: {e}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Backfill S3 uploads for published STAC projects"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Backfill a single project by UUID",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without making changes",
    )
    args = parser.parse_args()

    if not is_s3_configured():
        print("Error: S3 is not configured. Set AWS_S3_BUCKET_NAME in backend.env.")
        sys.exit(1)

    db = SessionLocal()

    try:
        # Query published projects
        query = select(Project).where(
            Project.is_published == True,
            Project.is_active == True,
        )
        if args.project_id:
            query = query.where(Project.id == UUID(args.project_id))

        projects = db.execute(query).scalars().all()

        if not projects:
            print("No published projects found to backfill.")
            return

        print(f"Found {len(projects)} published project(s) to process")
        if args.dry_run:
            print("[DRY RUN MODE - no changes will be made]\n")

        success_count = 0
        error_count = 0

        for project in projects:
            try:
                ok = backfill_project(db, project, dry_run=args.dry_run)
                if ok:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"  Error: {e}")
                db.rollback()

        print(f"\nBackfill complete:")
        print(f"  Success: {success_count}")
        print(f"  Errors: {error_count}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
