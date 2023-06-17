from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/{project_id}")
async def read_project(project_id: int):
    pass

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project():
    pass

@router.put("/")
async def update_project():
    pass

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project():
    pass
