from fastapi.testclient import TestClient

from ..main import app


client = TestClient(app)


def test_unknown_path():
    response = client.get("/unknown/path/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
