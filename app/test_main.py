from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_unknown_path():
    response = client.get("/unknown/path/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
