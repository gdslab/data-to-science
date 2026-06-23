from datetime import date, datetime
from typing import List

from pydantic import BaseModel, UUID4


class ViewsTrendPoint(BaseModel):
    week_start: date
    views: int


class DataProductStatRow(BaseModel):
    id: UUID4
    data_type: str
    project_id: UUID4
    project_name: str
    flight_id: UUID4
    flight_date: date
    views: int
    likes: int


class RecentActivityRow(BaseModel):
    id: UUID4
    data_type: str
    project_id: UUID4
    project_name: str
    owner_name: str
    flight_id: UUID4
    flight_date: date
    last_action_at: datetime


class OwnerStats(BaseModel):
    total_views: int
    total_likes: int
    data_product_count: int
    public_count: int
    project_count: int
    views_trend: List[ViewsTrendPoint]
    top_viewed: List[DataProductStatRow]
    top_liked: List[DataProductStatRow]


class ActivityCounts(BaseModel):
    viewed_count: int
    liked_count: int
    recently_viewed: List[RecentActivityRow]
    recently_liked: List[RecentActivityRow]


class ProfileStats(BaseModel):
    received: OwnerStats
    activity: ActivityCounts
