from datetime import date

from pydantic import BaseModel, UUID4


class ActivationFunnel(BaseModel):
    """Monotonic funnel from registration to first project.

    ``joined_project`` counts users on at least one active project by any route
    (created it, added directly, or added through a team). Project owners are
    given a member row when the project is created, so ``created_project`` is a
    strict subset of ``joined_project``.
    """

    signed_up: int
    email_confirmed: int
    approved: int
    joined_project: int
    created_project: int


class ActivitySummary(BaseModel):
    """Point-in-time activity snapshot for the admin dashboard header."""

    active_24h: int
    active_7d: int
    active_30d: int
    total_users: int
    funnel: ActivationFunnel


class ActivityTrendPoint(BaseModel):
    """A single day in the active-user time series."""

    snapshot_date: date
    active_24h: int
    active_7d: int
    active_30d: int
    new_users: int
    stickiness: float


class EngagementLeaderRow(BaseModel):
    """Per-user content/engagement totals for the power-user leaderboard."""

    user_id: UUID4
    name: str
    email: str
    project_count: int
    flight_count: int
    data_product_count: int
    total_views: int
    total_likes: int
    total_storage: int  # bytes of data products + raw data owned by the user
