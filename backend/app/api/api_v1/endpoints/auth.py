from fastapi import APIRouter, status

router = APIRouter()


@router.post("/login/")
async def login():
    pass

@router.post("/logout/", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    pass

@router.post("/changepassword/")
async def change_password():
    pass