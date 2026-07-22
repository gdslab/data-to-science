"""Seed projects for existing demo users so the engagement leaderboard fills up.

Development helper only. Gives every demo account (see ``seed_demo_activity.py``,
which creates users at ``DEMO_EMAIL_DOMAIN``) a handful of active projects so the
admin engagement leaderboard has enough ranked owners to page through.

Each project gets a real ``Location`` polygon and an owner ``ProjectMember`` row,
mirroring ``crud.project.create_with_owner``, but skips flights, data products,
and module rows — the leaderboard only counts projects here, and the lean shape
keeps ``--purge`` simple. Projects are identified as "demo" by their owner's
email domain, so nothing marks real users' projects.

Run ``--purge`` here BEFORE purging demo users in ``seed_demo_activity.py``:
``projects.owner_id`` has no cascade, so deleting a user who still owns projects
fails on the foreign key.

Examples:
    python /app/app/scripts/seed_demo_projects.py
    python /app/app/scripts/seed_demo_projects.py --min-projects 1 --max-projects 10 --seed 7
    python /app/app/scripts/seed_demo_projects.py --purge
"""

import argparse
import json
import logging
import sys
import uuid
import warnings
from datetime import datetime, timezone

from faker import Faker
from sqlalchemy import delete, func, select

warnings.filterwarnings("ignore", message="relationship .* will copy column")

from app.db.session import SessionLocal
from app.models.location import Location
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.enums.project_type import ProjectType
from app.schemas.role import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kept in sync with seed_demo_activity.py: the same accounts this script targets.
DEMO_EMAIL_DOMAIN = "d2s-demo.example.com"

# Bounding box the random project footprints fall inside (roughly the contiguous
# US). The exact location is irrelevant for dashboard counts; it only needs to be
# a valid polygon so the NOT NULL location_id can be satisfied.
_LON_RANGE = (-120.0, -80.0)
_LAT_RANGE = (30.0, 48.0)
_FOOTPRINT_DEGREES = 0.01


def _random_polygon(faker: Faker) -> dict:
    """Return a small closed square polygon as a GeoJSON geometry dict."""
    rng = faker.random
    lon = rng.uniform(*_LON_RANGE)
    lat = rng.uniform(*_LAT_RANGE)
    d = _FOOTPRINT_DEGREES
    ring = [
        [lon, lat],
        [lon + d, lat],
        [lon + d, lat + d],
        [lon, lat + d],
        [lon, lat],  # GeoJSON rings must close on the first vertex
    ]
    return {"type": "Polygon", "coordinates": [ring]}


def _project_created_at(faker: Faker, user_created_at: datetime) -> datetime:
    """Pick a project creation time between the owner's signup and now."""
    now = datetime.now(timezone.utc)
    owner_created = user_created_at
    if owner_created.tzinfo is None:
        owner_created = owner_created.replace(tzinfo=timezone.utc)
    # Clamp defensively in case a user's created_at is in the future.
    if owner_created >= now:
        return now
    return faker.date_time_between(
        start_date=owner_created, end_date=now, tzinfo=timezone.utc
    )


def seed(min_projects: int, max_projects: int, seed_value: int | None) -> None:
    if min_projects < 1 or max_projects < min_projects:
        logger.error("Require 1 <= --min-projects <= --max-projects.")
        sys.exit(1)

    faker = Faker()
    if seed_value is not None:
        faker.seed_instance(seed_value)
    rng = faker.random

    with SessionLocal() as session:
        try:
            with session.begin():
                demo_users = session.scalars(
                    select(User).where(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}"))
                ).all()
                if not demo_users:
                    logger.error(
                        "No demo users found. Run seed_demo_activity.py first."
                    )
                    sys.exit(1)

                owners_with_projects = set(
                    session.scalars(
                        select(Project.owner_id).where(
                            Project.owner_id.in_([u.id for u in demo_users])
                        )
                    ).all()
                )

                total = 0
                skipped = 0
                for user in demo_users:
                    # Idempotent: don't stack more projects onto a user that a
                    # previous run already seeded.
                    if user.id in owners_with_projects:
                        skipped += 1
                        continue

                    for _ in range(rng.randint(min_projects, max_projects)):
                        # Assign ids up front so the project can reference the
                        # location without an intermediate flush.
                        location_id = uuid.uuid4()
                        project_id = uuid.uuid4()
                        geometry = _random_polygon(faker)
                        geom = func.ST_Force2D(
                            func.ST_GeomFromGeoJSON(json.dumps(geometry))
                        )
                        session.add(Location(id=location_id, geom=geom))
                        session.add(
                            Project(
                                id=project_id,
                                title=f"{faker.city()} {faker.word()} survey"[:255],
                                description=faker.sentence(nb_words=8)[:300],
                                location_id=location_id,
                                owner_id=user.id,
                                is_active=True,
                                created_at=_project_created_at(
                                    faker, user.created_at
                                ),
                            )
                        )
                        session.add(
                            ProjectMember(
                                member_id=user.id,
                                project_type=ProjectType.PROJECT,
                                project_uuid=project_id,
                                role=Role.OWNER,
                            )
                        )
                        total += 1
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"Failed to seed demo projects: {e}")
            sys.exit(1)

    logger.info(
        "Seeded %d projects across %d demo users (%d already had projects, "
        "left untouched).",
        total,
        len(demo_users) - skipped,
        skipped,
    )


def purge() -> None:
    """Delete every project owned by a demo user, plus its location and members.

    Ordered to respect foreign keys: project_members and the projects themselves
    go before the locations they reference (``projects.location_id``).
    """
    with SessionLocal() as session:
        try:
            with session.begin():
                demo_user_ids = session.scalars(
                    select(User.id).where(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}"))
                ).all()
                if not demo_user_ids:
                    logger.info("No demo users found; nothing to purge.")
                    return

                rows = session.execute(
                    select(Project.id, Project.location_id).where(
                        Project.owner_id.in_(demo_user_ids)
                    )
                ).all()
                project_ids = [row[0] for row in rows]
                location_ids = [row[1] for row in rows]

                if not project_ids:
                    logger.info("No demo projects found; nothing to purge.")
                    return

                session.execute(
                    delete(ProjectMember).where(
                        ProjectMember.project_uuid.in_(project_ids)
                    )
                )
                session.execute(delete(Project).where(Project.id.in_(project_ids)))
                session.execute(
                    delete(Location).where(Location.id.in_(location_ids))
                )
        except Exception as e:
            logger.error(f"Failed to purge demo projects: {e}")
            sys.exit(1)

    logger.info("Removed %d demo projects and their locations.", len(project_ids))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed projects for demo users to populate the engagement leaderboard"
    )
    parser.add_argument(
        "--min-projects",
        type=int,
        default=1,
        help="Minimum projects per demo user (default: 1)",
    )
    parser.add_argument(
        "--max-projects",
        type=int,
        default=10,
        help="Maximum projects per demo user (default: 10)",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="RNG seed for reproducible output"
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Delete all projects owned by demo users instead of seeding",
    )

    args = parser.parse_args()

    if args.purge:
        purge()
    else:
        seed(
            min_projects=args.min_projects,
            max_projects=args.max_projects,
            seed_value=args.seed,
        )


if __name__ == "__main__":
    main()
