from fastapi import APIRouter, HTTPException, status

from app.schemas.user import get_fake_users, UserIn, UserInDB, UserOut

router = APIRouter()


def find_user_by_id(user_id: int):
    """Find user by a unique id.

    Args:
        user_id (int): Unique id for a user

    Returns:
        _type_: User model or None
    """
    return next(filter(lambda user: user["user_id"] == user_id, get_fake_users()), None)

@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserIn):
    hashed_password = "hash" + user_in.password  # not for production
    user_in_db = UserInDB(**user_in.dict(), hashed_password=hashed_password)
    return user_in_db

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_out: UserOut):
    existing_user = find_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_in_db = UserInDB(**{**get_fake_users()[user_id], **user_out.dict()})
    return user_in_db

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    existing_user = find_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    users_in_db = get_fake_users()
    users_in_db.pop(users_in_db.index(existing_user))
