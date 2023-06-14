from faker import Faker
from pydantic import BaseModel, EmailStr


fake = Faker()


def get_fake_users():
    """Generates list of five fake users. 
    Each user is represented by a dictionary.

    Returns:
        list: List of user dictionaries
    """
    Faker.seed(0)  # return same fake users every function call

    return [
        {
            "user_id": idx + 1,
            "hashed_password": fake.password(),
            "email": fake.email(),
            "full_name": fake.name()
        } for idx in range(0, 5)
    ]

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None

class UserIn(UserBase):
    password: str

class UserOut(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str