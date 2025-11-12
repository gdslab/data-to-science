from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.mail import fm
from app.tests.conftest import pytest_requires_mail


@pytest_requires_mail
def test_email_contact_message_to_support(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    subject = "Lorem ipsum odor amet, consectetuer adipiscing elit."
    message = """Lorem ipsum odor amet, consectetuer adipiscing elit. Ultrices quis 
    facilisis pulvinar nunc taciti senectus dictumst arcu sapien. Porttitor mauris 
    posuere enim tempor aptent a eu id. Neque justo varius neque penatibus vulputate. 
    Facilisi nulla blandit ut maecenas ligula feugiat nibh. Nisi molestie class montes, 
    urna neque finibus. Interdum urna fermentum et nascetur eros sed. Convallis proin 
    porta convallis eleifend; quisque sociosqu."""

    api_domain = settings.API_DOMAIN
    payload = {"topic": "bug_report", "subject": subject, "message": message}
    if fm:
        fm.config.SUPPRESS_SEND = 1
        with fm.record_messages() as outbox:
            response = client.post(f"{settings.API_V1_STR}/contact", json=payload)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(outbox) == 1
        assert (
            outbox[0]["from"]
            == settings.MAIL_FROM_NAME + " <" + settings.MAIL_FROM + ">"
        )
        assert outbox[0]["To"] == settings.MAIL_FROM
        assert (
            outbox[0]["Subject"]
            == f"Data to Science Contact Form: BUG REPORT ({api_domain})"
        )


@pytest_requires_mail
def test_email_contact_message_with_too_few_characters(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    subject = "Iota"
    message = "Not enough characters"

    payload = {"subject": subject, "message": message}
    response = client.post(f"{settings.API_V1_STR}/contact", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest_requires_mail
def test_email_contact_message_with_too_many_characters(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    subject = "Lorem ipsum odor amet, consectetuer adipiscing elit." * 2
    message = (
        """Lorem ipsum odor amet, consectetuer adipiscing elit. Ultrices quis 
    facilisis pulvinar nunc taciti senectus dictumst arcu sapien. Porttitor mauris 
    posuere enim tempor aptent a eu id. Neque justo varius neque penatibus vulputate. 
    Facilisi nulla blandit ut maecenas ligula feugiat nibh. Nisi molestie class montes, 
    urna neque finibus. Interdum urna fermentum et nascetur eros sed. Convallis proin 
    porta convallis eleifend; quisque sociosqu."""
        * 3
    )

    payload = {"subject": subject, "message": message}
    response = client.post(f"{settings.API_V1_STR}/contact", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest_requires_mail
def test_email_contact_message_without_email_enabled_on_instance(
    client: TestClient, db: Session, normal_user_access_token: str, monkeypatch
) -> None:
    subject = "Lorem ipsum odor amet, consectetuer adipiscing elit."
    message = """Lorem ipsum odor amet, consectetuer adipiscing elit. Ultrices quis
    facilisis pulvinar nunc taciti senectus dictumst arcu sapien. Porttitor mauris
    posuere enim tempor aptent a eu id. Neque justo varius neque penatibus vulputate.
    Facilisi nulla blandit ut maecenas ligula feugiat nibh. Nisi molestie class montes,
    urna neque finibus. Interdum urna fermentum et nascetur eros sed. Convallis proin
    porta convallis eleifend; quisque sociosqu."""

    payload = {"topic": "bug_report", "subject": subject, "message": message}
    if fm:
        fm.config.SUPPRESS_SEND = 1
        # Temporarily disable MAIL_ENABLED to test the error case
        monkeypatch.setattr(settings, "MAIL_ENABLED", False)
        with fm.record_messages():
            response = client.post(f"{settings.API_V1_STR}/contact", json=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
