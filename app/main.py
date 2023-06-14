from fastapi import FastAPI, HTTPException, status

from .models.user import get_fake_users, UserIn, UserInDB, UserOut


app = FastAPI()


def find_user_by_id(user_id: int):
    """Find user by a unique id.

    Args:
        user_id (int): Unique id for a user

    Returns:
        _type_: User model or None
    """
    return next(filter(lambda user: user["user_id"] == user_id, get_fake_users()), None)

@app.get("/users/{user_id}/", response_model=UserOut, tags=["users"])
async def read_user(user_id: int):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["users"])
async def create_user(user_in: UserIn):
    hashed_password = "hash" + user_in.password  # not for production
    user_in_db = UserInDB(**user_in.dict(), hashed_password=hashed_password)
    return user_in_db

@app.put("/users/{user_id}/", response_model=UserOut, tags=["users"])
async def update_user(user_id: int, user_out: UserOut):
    existing_user = find_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_in_db = UserInDB(**{**get_fake_users()[user_id], **user_out.dict()})
    return user_in_db

@app.delete("/users/{user_id}/", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
async def delete_user(user_id: int):
    existing_user = find_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    users_in_db = get_fake_users()
    users_in_db.pop(users_in_db.index(existing_user))
