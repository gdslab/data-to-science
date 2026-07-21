from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models import (
    ActivitySnapshot,
    DataProduct,
    DataProductLike,
    DataProductView,
    Flight,
    Project,
    ProjectMember,
    RawData,
    User,
)
from app.models.enums.project_type import ProjectType
from app.schemas.activity import (
    ActivationFunnel,
    ActivitySummary,
    ActivityTrendPoint,
    EngagementLeaderRow,
)

LeaderboardMetric = Literal[
    "projects", "flights", "data_products", "views", "likes", "storage"
]

# Maps the public metric name to the EngagementLeaderRow field it sorts on.
_METRIC_TO_FIELD: Dict[str, str] = {
    "projects": "project_count",
    "flights": "flight_count",
    "data_products": "data_product_count",
    "views": "total_views",
    "likes": "total_likes",
    "storage": "total_storage",
}


def get_activity_summary(db: Session) -> ActivitySummary:
    """Current active-user counts plus the signup -> first-project funnel.

    Active counts are derived from ``users.last_activity_at`` (maintained by the
    request middleware). The funnel stages are nested subsets so the bars are
    strictly decreasing: every email-confirmed user signed up, every approved
    user is confirmed, every user on a project is approved + confirmed, and
    every project creator is also a project member (owners receive a member row
    when the project is created).
    """
    now = datetime.now(timezone.utc)

    # Single round trip with scalar subqueries, mirroring crud_admin.get_site_statistics.
    summary_query = select(
        select(func.count(User.id))
        .where(User.last_activity_at >= now - timedelta(days=1))
        .scalar_subquery()
        .label("active_24h"),
        select(func.count(User.id))
        .where(User.last_activity_at >= now - timedelta(days=7))
        .scalar_subquery()
        .label("active_7d"),
        select(func.count(User.id))
        .where(User.last_activity_at >= now - timedelta(days=30))
        .scalar_subquery()
        .label("active_30d"),
        select(func.count(User.id)).scalar_subquery().label("signed_up"),
        select(func.count(User.id))
        .where(User.is_email_confirmed)
        .scalar_subquery()
        .label("email_confirmed"),
        select(func.count(User.id))
        .where(and_(User.is_email_confirmed, User.is_approved))
        .scalar_subquery()
        .label("approved"),
        select(func.count(func.distinct(ProjectMember.member_id)))
        .select_from(ProjectMember)
        .join(User, User.id == ProjectMember.member_id)
        .join(Project, Project.id == ProjectMember.project_uuid)
        .where(
            and_(
                ProjectMember.project_type == ProjectType.PROJECT,
                Project.is_active,
                User.is_email_confirmed,
                User.is_approved,
            )
        )
        .scalar_subquery()
        .label("joined_project"),
        select(func.count(func.distinct(Project.owner_id)))
        .select_from(Project)
        .join(User, User.id == Project.owner_id)
        .where(and_(Project.is_active, User.is_email_confirmed, User.is_approved))
        .scalar_subquery()
        .label("created_project"),
    )

    result = db.execute(summary_query).one()

    return ActivitySummary(
        active_24h=result.active_24h,
        active_7d=result.active_7d,
        active_30d=result.active_30d,
        total_users=result.approved,
        funnel=ActivationFunnel(
            signed_up=result.signed_up,
            email_confirmed=result.email_confirmed,
            approved=result.approved,
            joined_project=result.joined_project,
            created_project=result.created_project,
        ),
    )


def get_engagement_leaderboard(
    db: Session, *, metric: LeaderboardMetric = "data_products", limit: int = 10
) -> List[EngagementLeaderRow]:
    """Top users ranked by content created or engagement received.

    Everything is attributed to the project owner (``Project.owner_id``),
    consistent with the existing ``/admin/project_statistics`` convention:
    projects, their flights and data products, and the views/likes/storage those
    accrue. Every metric counts fully live content only: the data product, its
    flight, and its project must all be active. Counts are gathered with separate
    GROUP BY queries (rather than one wide join) so that, e.g., a project with
    many flights and many views does not multiply either total.
    """
    project_counts = dict(
        db.execute(
            select(Project.owner_id, func.count(Project.id))
            .where(Project.is_active)
            .group_by(Project.owner_id)
        ).all()
    )
    flight_counts = dict(
        db.execute(
            select(Project.owner_id, func.count(Flight.id))
            .select_from(Flight)
            .join(Project, Project.id == Flight.project_id)
            .where(and_(Flight.is_active, Project.is_active))
            .group_by(Project.owner_id)
        ).all()
    )
    data_product_counts = dict(
        db.execute(
            select(Project.owner_id, func.count(DataProduct.id))
            .select_from(DataProduct)
            .join(Flight, Flight.id == DataProduct.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(and_(DataProduct.is_active, Flight.is_active, Project.is_active))
            .group_by(Project.owner_id)
        ).all()
    )
    view_counts = dict(
        db.execute(
            select(Project.owner_id, func.count(DataProductView.id))
            .select_from(DataProductView)
            .join(DataProduct, DataProduct.id == DataProductView.data_product_id)
            .join(Flight, Flight.id == DataProduct.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(and_(DataProduct.is_active, Flight.is_active, Project.is_active))
            .group_by(Project.owner_id)
        ).all()
    )
    like_counts = dict(
        db.execute(
            select(Project.owner_id, func.count(DataProductLike.id))
            .select_from(DataProductLike)
            .join(DataProduct, DataProduct.id == DataProductLike.data_product_id)
            .join(Flight, Flight.id == DataProduct.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(and_(DataProduct.is_active, Flight.is_active, Project.is_active))
            .group_by(Project.owner_id)
        ).all()
    )
    # Data usage = stored data product + raw data byte sizes (NULL treated as 0),
    # summed separately so the two never multiply each other.
    data_product_storage = dict(
        db.execute(
            select(
                Project.owner_id,
                func.coalesce(func.sum(DataProduct.file_size), 0),
            )
            .select_from(DataProduct)
            .join(Flight, Flight.id == DataProduct.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(and_(DataProduct.is_active, Flight.is_active, Project.is_active))
            .group_by(Project.owner_id)
        ).all()
    )
    raw_data_storage = dict(
        db.execute(
            select(
                Project.owner_id,
                func.coalesce(func.sum(RawData.file_size), 0),
            )
            .select_from(RawData)
            .join(Flight, Flight.id == RawData.flight_id)
            .join(Project, Project.id == Flight.project_id)
            .where(and_(RawData.is_active, Flight.is_active, Project.is_active))
            .group_by(Project.owner_id)
        ).all()
    )

    user_ids = (
        set(project_counts)
        | set(flight_counts)
        | set(data_product_counts)
        | set(view_counts)
        | set(like_counts)
        | set(data_product_storage)
        | set(raw_data_storage)
    )
    if not user_ids:
        return []

    rows = [
        {
            "user_id": user_id,
            "project_count": project_counts.get(user_id, 0),
            "flight_count": flight_counts.get(user_id, 0),
            "data_product_count": data_product_counts.get(user_id, 0),
            "total_views": view_counts.get(user_id, 0),
            "total_likes": like_counts.get(user_id, 0),
            "total_storage": data_product_storage.get(user_id, 0)
            + raw_data_storage.get(user_id, 0),
        }
        for user_id in user_ids
    ]

    sort_field = _METRIC_TO_FIELD[metric]
    # Tie-break on data_product_count then user_id for a stable ordering.
    rows.sort(
        key=lambda row: (
            row[sort_field],
            row["data_product_count"],
            str(row["user_id"]),
        ),
        reverse=True,
    )
    top_rows = rows[:limit]

    top_ids = [row["user_id"] for row in top_rows]
    user_map = {
        user.id: (user.full_name, user.email)
        for user in db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(top_ids))
        ).all()
    }

    leaderboard = []
    for row in top_rows:
        name, email = user_map.get(row["user_id"], ("Unknown user", ""))
        leaderboard.append(
            EngagementLeaderRow(
                user_id=row["user_id"],
                name=name,
                email=email,
                project_count=row["project_count"],
                flight_count=row["flight_count"],
                data_product_count=row["data_product_count"],
                total_views=row["total_views"],
                total_likes=row["total_likes"],
                total_storage=row["total_storage"],
            )
        )
    return leaderboard


def get_activity_trends(db: Session, *, days: int = 90) -> List[ActivityTrendPoint]:
    """Active-user time series from recorded daily snapshots (oldest -> newest)."""
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)
    snapshots = (
        db.execute(
            select(ActivitySnapshot)
            .where(ActivitySnapshot.snapshot_date >= cutoff)
            .order_by(ActivitySnapshot.snapshot_date)
        )
        .scalars()
        .all()
    )

    points = []
    for snapshot in snapshots:
        stickiness = (
            round(snapshot.active_24h / snapshot.active_30d, 3)
            if snapshot.active_30d
            else 0.0
        )
        points.append(
            ActivityTrendPoint(
                snapshot_date=snapshot.snapshot_date,
                active_24h=snapshot.active_24h,
                active_7d=snapshot.active_7d,
                active_30d=snapshot.active_30d,
                new_users=snapshot.new_users,
                stickiness=stickiness,
            )
        )
    return points


def create_activity_snapshot(db: Session) -> ActivitySnapshot:
    """Compute and persist today's activity counts (idempotent per day).

    Re-running for a date that already has a row updates it in place, so a manual
    re-trigger or a retried Celery task never creates duplicates. The counts are
    always measured as of now, so there is no way to record a past date.
    """
    now = datetime.now(timezone.utc)
    target_date = now.date()

    active_24h = db.execute(
        select(func.count(User.id)).where(
            User.last_activity_at >= now - timedelta(days=1)
        )
    ).scalar_one()
    active_7d = db.execute(
        select(func.count(User.id)).where(
            User.last_activity_at >= now - timedelta(days=7)
        )
    ).scalar_one()
    active_30d = db.execute(
        select(func.count(User.id)).where(
            User.last_activity_at >= now - timedelta(days=30)
        )
    ).scalar_one()
    new_users = db.execute(
        select(func.count(User.id)).where(func.date(User.created_at) == target_date)
    ).scalar_one()
    total_users = db.execute(
        select(func.count(User.id)).where(
            and_(User.is_approved, User.is_email_confirmed)
        )
    ).scalar_one()

    snapshot = db.execute(
        select(ActivitySnapshot).where(ActivitySnapshot.snapshot_date == target_date)
    ).scalar_one_or_none()

    if snapshot is None:
        snapshot = ActivitySnapshot(snapshot_date=target_date)
        db.add(snapshot)

    snapshot.active_24h = active_24h
    snapshot.active_7d = active_7d
    snapshot.active_30d = active_30d
    snapshot.new_users = new_users
    snapshot.total_users = total_users

    db.commit()
    db.refresh(snapshot)
    return snapshot
