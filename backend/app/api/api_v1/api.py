from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    flights,
    locations,
    projects,
    project_members,
    data_products,
    raw_data,
    teams,
    team_members,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    flights.router, prefix="/projects/{project_id}/flights", tags=["flights"]
)
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(
    project_members.router,
    prefix="/projects/{project_id}/members",
    tags=["project_members"],
)
api_router.include_router(
    data_products.router,
    prefix="/projects/{project_id}/flights/{flight_id}/data_products",
    tags=["data_products"],
)
api_router.include_router(
    raw_data.router,
    prefix="/projects/{project_id}/flights/{flight_id}/raw_data",
    tags=["raw_data"],
)
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(
    team_members.router, prefix="/teams/{team_id}/members", tags=["team_members"]
)
api_router.include_router(users.router, prefix="/users", tags=["users"])
