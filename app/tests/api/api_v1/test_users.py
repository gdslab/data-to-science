from faker import Faker
from fastapi.testclient import TestClient

from app.core.config import settings
from app.schemas.user import get_fake_users, UserInDB, UserOut

faker = Faker()
Faker.seed(42)


def test_read_user(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/users/1/")
    assert response.status_code == 200
    assert response.json()["email"] == get_fake_users()[0]["email"]

def test_read_user_not_found(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/users/9999/")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_read_user_does_not_expose_private_fields(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/users/1/")
    assert response.status_code == 200
    assert response.json() == UserOut(**get_fake_users()[0])

def test_create_user(client: TestClient):
    new_user_body = {
        "email": faker.email(),
        "password": faker.password(),
        "full_name": faker.name()
    }

    response = client.post(f"{settings.API_V1_STR}/users/", json=new_user_body)
    assert response.status_code == 201
    assert response.json() == UserOut(**new_user_body)

def test_update_user(client: TestClient):
    existing_user = get_fake_users()[0]
    updated_user_body = {"email": faker.email(), "full_name": existing_user["full_name"]}

    response = client.put(f"{settings.API_V1_STR}/users/1/", json=updated_user_body)
    assert response.status_code == 200
    assert response.json()["email"] != existing_user["email"]

def test_update_user_not_found(client: TestClient):
    updated_user_body = {"email": faker.email(), "full_name": faker.name()}

    response = client.put(f"{settings.API_V1_STR}/users/9999/", json=updated_user_body)
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_delete_user(client: TestClient):
    response = client.delete(f"{settings.API_V1_STR}/users/1/")
    assert response.status_code == 204

def test_delete_user_not_found(client: TestClient):
    response = client.delete(f"{settings.API_V1_STR}/users/9999/")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
