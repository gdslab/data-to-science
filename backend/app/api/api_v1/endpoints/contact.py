import html
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api import deps, mail
from app.models.user import User
from app.schemas.contact import ContactForm

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def email_contact_message_to_support(
    contact_form: ContactForm,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_approved_user),
) -> Any:
    topic = " ".join(html.escape(contact_form.topic.strip()).split("_")).upper()
    contact_email = current_user.email
    contact_name = " ".join([current_user.first_name, current_user.last_name])
    sender = {"name": contact_name, "email": contact_email}

    mail.send_contact_email(
        background_tasks=background_tasks,
        topic=topic,
        subject=html.escape(contact_form.subject.strip()),
        message=html.escape(contact_form.message.strip()),
        sender=sender,
    )
