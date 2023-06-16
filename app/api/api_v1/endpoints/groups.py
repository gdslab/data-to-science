from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/{group_id}")
async def read_group(group_id: int):
    pass

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_group():
    pass

@router.put("/")
async def update_group():
    pass

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group():
    pass
