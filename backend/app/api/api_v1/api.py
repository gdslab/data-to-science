from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    admin,
    auth,
    breedbase_connections,
    campaigns,
    contact,
    file_permission,
    flights,
    health,
    iforester,
    locations,
    public,
    projects,
    project_members,
    data_products,
    raw_data,
    style,
    teams,
    team_members,
    tusd,
    utils,
    users,
    vector_layers,
)

api_router = APIRouter()
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])
api_router.include_router(
    breedbase_connections.router,
    prefix="/projects/{project_id}/breedbase-connections",
    tags=["breedbase_connections"],
)
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(
    campaigns.router, prefix="/projects/{project_id}/campaigns", tags=["campaigns"]
)
api_router.include_router(
    flights.router, prefix="/projects/{project_id}/flights", tags=["flights"]
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
api_router.include_router(
    file_permission.router,
    prefix="/projects/{project_id}/flights/{flight_id}/data_products/{data_product_id}/file_permission",
    tags=["file_permission"],
)

api_router.include_router(
    style.router,
    prefix="/projects/{project_id}/flights/{flight_id}/data_products/{data_product_id}/style",
    tags=["style"],
)
api_router.include_router(
    utils.router,
    prefix="/projects/{project_id}/flights/{flight_id}/data_products/{data_product_id}/utils",
    tags=["utils"],
)
api_router.include_router(
    iforester.router, prefix="/projects/{project_id}/iforester", tags=["iforester"]
)
api_router.include_router(
    project_members.router,
    prefix="/projects/{project_id}/members",
    tags=["project_members"],
)
api_router.include_router(
    vector_layers.router,
    prefix="/projects/{project_id}/vector_layers",
    tags=["vector_layers"],
)
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(
    team_members.router, prefix="/teams/{team_id}/members", tags=["team_members"]
)
api_router.include_router(tusd.router, prefix="/tusd", tags=["tusd"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
