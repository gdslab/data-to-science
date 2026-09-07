from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.utils import titiler as titiler_utils


def test_check_health_reports_titiler_status(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/health")

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["status"] == "healthy"
    assert "version" in response_data["titiler"]
    assert "compatible" in response_data["titiler"]


def test_check_health_reports_probed_titiler_version(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(titiler_utils.titiler_status, "version", "2.2.1")
    monkeypatch.setattr(titiler_utils.titiler_status, "compatible", True)

    response = client.get(f"{settings.API_V1_STR}/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["titiler"] == {"version": "2.2.1", "compatible": True}
