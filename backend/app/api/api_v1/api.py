from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, datasets, projects, teams, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    datasets.router, prefix="/projects/{project_id}/datasets", tags=["datasets"]
)
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
