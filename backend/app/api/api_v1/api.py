from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    flights,
    locations,
    projects,
    data_products,
    teams,
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
    data_products.router,
    prefix="/projects/{project_id}/flights/{flight_id}/data_products",
    tags=["data_products"],
)
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
