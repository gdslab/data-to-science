"""Seed demo users and activity snapshots for exercising the admin dashboard.

Development helper only. Creates users whose ``created_at`` dates span the last
few years with randomized activation state and recent activity, plus a run of
daily activity snapshots, so the signup and activity sections of
``DashboardActivity`` have realistic data to render.

Every account is created at ``DEMO_EMAIL_DOMAIN`` and flagged ``is_demo``, so
``--purge`` can remove them (and their snapshots) without touching real users.

Examples:
    python /app/app/scripts/seed_demo_activity.py
    python /app/app/scripts/seed_demo_activity.py --count 250 --years 5 --seed 7
    python /app/app/scripts/seed_demo_activity.py --purge
"""

import argparse
import logging
import random
import sys
import warnings
from datetime import date, datetime, timedelta, timezone

from faker import Faker
from pydantic import EmailStr, TypeAdapter
from sqlalchemy import delete, select

warnings.filterwarnings("ignore", message="relationship .* will copy column")

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.activity_snapshot import ActivitySnapshot
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Must be a domain that email-validator accepts, because the admin endpoints
# serialize users through EmailStr. RFC 2606 special-use names (.invalid, .test,
# .localhost, .example) are rejected outright and would break the admin user list
# for every seeded row. A subdomain of example.com is reserved for documentation
# yet still validates.
DEMO_EMAIL_DOMAIN = "d2s-demo.example.com"
DEMO_PASSWORD = "demopassword123"

# Validates generated addresses at build time so a bad domain fails loudly here
# rather than on the first admin page load.
_EMAIL_ADAPTER = TypeAdapter(EmailStr)

# Share of accounts that reach each activation stage. Each stage is a subset of
# the one before it, matching how the dashboard funnel nests its bars.
CONFIRM_RATE = 0.85
APPROVE_RATE = 0.80

# How recently each user was last active. Weights are chosen so the 24h / 7d /
# 30d cards and the leaderboard all have a meaningful population.
ACTIVITY_BUCKETS: list[tuple[str, int]] = [
    ("today", 12),  # counted in DAU / WAU / MAU
    ("this_week", 14),  # WAU / MAU
    ("this_month", 20),  # MAU only
    ("stale", 34),  # active at some point, but outside every window
    ("never", 20),  # signed up and never returned
]


def _pick_signup_dates(rng: random.Random, count: int, years: int) -> list[datetime]:
    """Return signup timestamps skewed toward recent months, with burst days.

    Growth is weighted so later months get more signups than early ones, and a
    handful of days receive a cluster of accounts (think workshop sign-ups) so
    the calendar heatmap spans its full color scale instead of showing a flat
    field of ones.
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365 * years)
    span_days = (now - start).days

    # Weight each day by how far along the window it falls, so signup volume
    # ramps up over time rather than staying uniform.
    day_weights = [1 + 4 * (day / span_days) for day in range(span_days + 1)]

    burst_count = max(1, count // 20)
    burst_days = rng.sample(range(span_days + 1), burst_count)
    for day in burst_days:
        day_weights[day] *= 25

    chosen_days = rng.choices(range(span_days + 1), weights=day_weights, k=count)

    return [
        start
        + timedelta(
            days=day,
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        for day in chosen_days
    ]


def _pick_last_activity(
    rng: random.Random, created_at: datetime, now: datetime
) -> datetime | None:
    """Return a last-activity timestamp for one user, or None if never active."""
    bucket = rng.choices(
        [name for name, _ in ACTIVITY_BUCKETS],
        weights=[weight for _, weight in ACTIVITY_BUCKETS],
    )[0]

    if bucket == "never":
        return None
    if bucket == "today":
        activity = now - timedelta(minutes=rng.randint(5, 23 * 60))
    elif bucket == "this_week":
        activity = now - timedelta(days=rng.randint(1, 6), hours=rng.randint(0, 23))
    elif bucket == "this_month":
        activity = now - timedelta(days=rng.randint(7, 29), hours=rng.randint(0, 23))
    else:
        activity = now - timedelta(days=rng.randint(31, 400), hours=rng.randint(0, 23))

    # A user cannot have been active before signing up.
    return max(activity, created_at)


def _build_users(faker: Faker, count: int, years: int) -> list[User]:
    """Build (unsaved) demo users with varied signup dates and activation state."""
    now = datetime.now(timezone.utc)
    # Faker's Random drives the distributions too, so one seed reproduces the
    # entire dataset.
    rng = faker.random
    # Hash once and reuse: bcrypt is deliberately slow and every demo account
    # shares the same throwaway password anyway.
    hashed_password = get_password_hash(DEMO_PASSWORD)

    users = []
    for created_at in _pick_signup_dates(rng, count, years):
        first_name = faker.first_name()
        last_name = faker.last_name()
        is_email_confirmed = rng.random() < CONFIRM_RATE
        is_approved = is_email_confirmed and rng.random() < APPROVE_RATE
        last_activity_at = _pick_last_activity(rng, created_at, now)

        email = _EMAIL_ADAPTER.validate_python(
            faker.unique.email(domain=DEMO_EMAIL_DOMAIN)
        )

        users.append(
            User(
                email=email,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                is_approved=is_approved,
                is_demo=True,
                is_email_confirmed=is_email_confirmed,
                created_at=created_at,
                last_login_at=last_activity_at,
                last_activity_at=last_activity_at,
            )
        )

    return users


def _build_snapshots(
    rng: random.Random, users: list[User], days: int
) -> list[ActivitySnapshot]:
    """Build a daily DAU/WAU/MAU series ending yesterday.

    Real snapshots are recorded once per day going forward and cannot be
    backfilled, so the trend chart is empty on a fresh database. These rows
    synthesize that history: counts scale with how many demo accounts existed on
    each date and wobble day to day, always keeping 24h <= 7d <= 30d.
    """
    today = datetime.now(timezone.utc).date()
    signup_dates = sorted(user.created_at.date() for user in users)
    activated_dates = sorted(
        user.created_at.date()
        for user in users
        if user.is_approved and user.is_email_confirmed
    )

    snapshots = []
    for offset in range(days, 0, -1):
        snapshot_date = today - timedelta(days=offset)
        existing = sum(1 for day in signup_dates if day <= snapshot_date)
        activated = sum(1 for day in activated_dates if day <= snapshot_date)
        new_users = sum(1 for day in signup_dates if day == snapshot_date)

        # Weekday engagement runs higher than weekends; add noise on top.
        weekday_factor = 0.65 if snapshot_date.weekday() >= 5 else 1.0
        active_30d = round(existing * rng.uniform(0.30, 0.42))
        active_7d = round(active_30d * rng.uniform(0.45, 0.65) * weekday_factor)
        active_24h = round(active_7d * rng.uniform(0.25, 0.45) * weekday_factor)

        snapshots.append(
            ActivitySnapshot(
                snapshot_date=snapshot_date,
                active_24h=active_24h,
                active_7d=active_7d,
                active_30d=active_30d,
                new_users=new_users,
                total_users=activated,
            )
        )

    return snapshots


def seed(count: int, years: int, snapshot_days: int, seed_value: int | None) -> None:
    faker = Faker()
    if seed_value is not None:
        faker.seed_instance(seed_value)

    with SessionLocal() as session:
        try:
            with session.begin():
                existing = session.scalar(
                    select(User).where(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}"))
                )
                if existing:
                    logger.error(
                        "Demo users already exist. Run with --purge first to "
                        "replace them."
                    )
                    sys.exit(1)

                users = _build_users(faker, count, years)
                session.add_all(users)

                if snapshot_days > 0:
                    snapshot_dates = _snapshot_dates(snapshot_days)
                    already_recorded = set(
                        session.scalars(
                            select(ActivitySnapshot.snapshot_date).where(
                                ActivitySnapshot.snapshot_date.in_(snapshot_dates)
                            )
                        ).all()
                    )
                    if already_recorded:
                        logger.warning(
                            "Skipping %d snapshot date(s) that are already "
                            "recorded.",
                            len(already_recorded),
                        )
                    session.add_all(
                        snapshot
                        for snapshot in _build_snapshots(
                            faker.random, users, snapshot_days
                        )
                        if snapshot.snapshot_date not in already_recorded
                    )
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"Failed to seed demo activity: {e}")
            sys.exit(1)

    logger.info(
        "Seeded %d demo users over the last %d years and %d daily snapshots.",
        count,
        years,
        snapshot_days,
    )


def _snapshot_dates(days: int) -> list[date]:
    today = datetime.now(timezone.utc).date()
    return [today - timedelta(days=offset) for offset in range(days, 0, -1)]


def purge(snapshot_days: int) -> None:
    """Delete every demo account and the snapshot window this script writes.

    Snapshots carry no origin marker, so this clears *every* row in the trailing
    ``snapshot_days`` window, including any the Celery beat task recorded. Pass
    ``--snapshot-days 0`` to remove only the demo users.
    """
    with SessionLocal() as session:
        try:
            with session.begin():
                result = session.execute(
                    delete(User).where(User.email.like(f"%@{DEMO_EMAIL_DOMAIN}"))
                )
                snapshot_result = session.execute(
                    delete(ActivitySnapshot).where(
                        ActivitySnapshot.snapshot_date.in_(
                            _snapshot_dates(snapshot_days)
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Failed to purge demo activity: {e}")
            sys.exit(1)

    logger.info(
        "Removed %d demo users and %d activity snapshots.",
        result.rowcount,
        snapshot_result.rowcount,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed demo users and activity snapshots for the admin dashboard"
    )
    parser.add_argument(
        "--count", type=int, default=100, help="Number of demo users (default: 100)"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="Span signups over this many trailing years (default: 3)",
    )
    parser.add_argument(
        "--snapshot-days",
        type=int,
        default=120,
        help="Daily activity snapshots to backfill; 0 to skip (default: 120)",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="RNG seed for reproducible output"
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help=(
            "Delete demo users instead of seeding, along with every snapshot in "
            "the trailing --snapshot-days window"
        ),
    )

    args = parser.parse_args()

    if args.purge:
        purge(snapshot_days=args.snapshot_days)
    else:
        seed(
            count=args.count,
            years=args.years,
            snapshot_days=args.snapshot_days,
            seed_value=args.seed,
        )


if __name__ == "__main__":
    main()
