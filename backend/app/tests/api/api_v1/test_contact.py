from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.mail import fm


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
        assert outbox[0]["Subject"] == "BUG REPORT: D2S Contact Form Submission"


def test_email_contact_message_with_too_few_characters(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    subject = "Iota"
    message = "Not enough characters"

    payload = {"subject": subject, "message": message}
    response = client.post(f"{settings.API_V1_STR}/contact", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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
