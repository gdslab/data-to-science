from typing import Any, Dict, Optional

from fastapi import BackgroundTasks
from pydantic import EmailStr

from app.api.deps import send_email
from app.core.config import settings


def send_email_confirmation(
    background_tasks: BackgroundTasks,
    first_name: str,
    email: EmailStr,
    confirmation_token: str,
) -> None:
    confirmation_url = (
        settings.API_DOMAIN + settings.API_V1_STR + "/auth/confirm-email?"
    )
    confirmation_url += f"token={confirmation_token}"

    confirmation_btn = "<button style='display: inline-block;outline: none;"
    confirmation_btn += "border-radius: 3px;font-size: 14px;"
    confirmation_btn += "font-weight: 500;line-height: 16px;padding: 2px 16px;"
    confirmation_btn += "height: 38px;min-width: 96px;min-height: 38px;border: none;"
    confirmation_btn += "color: #fff;background-color: rgb(88, 101, 242);'>"
    confirmation_btn += "Confirm Email</button>"

    content = f"<p>Hi {first_name},</p>"
    content += (
        "<p>Thank you for creating an account with Data to Science. Please click the button below "
        "to confirm your email address.<br /><br />"
        f"<a href='{confirmation_url}' target='_blank'>{confirmation_btn}</a>"
        "<br /><br />"
        "The confirmation button will expire in 1 hour. If you do not respond within 1 "
        "hour, you will need to request a new confirmation email.<br /><br />"
        "If you have any questions, please reach out to support at "
        f"{settings.MAIL_FROM}.</p>"
        "<p>-Data to Science Support</p>"
    )

    send_email(
        subject="Welcome to Data to Science - please confirm your email",
        recipients=[email],
        body=content,
        background_tasks=background_tasks,
    )


def send_password_recovery(
    background_tasks: BackgroundTasks,
    first_name: str,
    email: EmailStr,
    recovery_token: str,
) -> None:
    recover_url = settings.API_DOMAIN + "/auth/resetpassword?"
    recover_url += f"token={recovery_token}"

    recover_btn = "<button style='display: inline-block;outline: none;"
    recover_btn += "border-radius: 3px;font-size: 14px;"
    recover_btn += "font-weight: 500;line-height: 16px;padding: 2px 16px;"
    recover_btn += "height: 38px;min-width: 96px;min-height: 38px;border: none;"
    recover_btn += "color: #fff;background-color: rgb(88, 101, 242);'>"
    recover_btn += "Reset Password</button>"

    content = f"<p>Hi {first_name},</p>"
    content += (
        "<p>Someone requested a password reset for your Data to Science account. To reset your "
        "password, please click the button below.<br /><br />"
        f"<a href='{recover_url}' target='_blank'>{recover_btn}</a>"
        "<br /><br />"
        "After clicking the button, you will be taken to a page where you can reset "
        "your password. If you do not respond within 1 hour, you will need to request "
        "a new password reset email. If you did not make this request, you may "
        "ignore this email.<br /><br />"
        "If you have any questions, please reach out to support at "
        f"{settings.MAIL_FROM}.</p>"
        "<p>-Data to Science Support</p>"
    )

    send_email(
        subject="Reset your Data to Science password",
        recipients=[email],
        body=content,
        background_tasks=background_tasks,
    )


def send_admins_new_registree_notification(
    background_tasks: BackgroundTasks,
    email: EmailStr,
    first_name: str,
    last_name: str,
    registration_intent: Optional[str],
    approve_token: str,
) -> None:
    admin_emails = settings.MAIL_ADMINS.split(",")

    approve_url = settings.API_DOMAIN + settings.API_V1_STR + "/auth/approve-account?"
    approve_url += f"token={approve_token}"

    approve_btn = "<button style='display: inline-block;outline: none;"
    approve_btn += "border-radius: 3px;font-size: 14px;"
    approve_btn += "font-weight: 500;line-height: 16px;padding: 2px 16px;"
    approve_btn += "height: 38px;min-width: 96px;min-height: 38px;border: none;"
    approve_btn += "color: #fff;background-color: rgb(88, 101, 242);'>"
    approve_btn += "Approve</button>"

    content = (
        "<p>Data to Science Support Admins,</p>"
        f"<p>A new account is awaiting approval. Please approve {first_name} {last_name}'s "
        f"({email}) account within 24 hours of receiving this notification. "
        "No action is needed to deny the account.<br /><br />"
    )

    if registration_intent:
        content += (
            f"<p><strong>Registration Intent:</strong></p>"
            f"<blockquote>{registration_intent}</blockquote><br />"
        )

    content += (
        f"<a href='{approve_url}' target='_blank'>{approve_btn}</a><br /><br />"
        "<p>-Data to Science Support</p>"
    )

    subject = "New Data to Science account awaiting approval"

    api_domain = settings.API_DOMAIN

    subject = f"{subject} ({api_domain})"

    send_email(
        subject=subject,
        recipients=admin_emails,
        body=content,
        background_tasks=background_tasks,
    )


def send_account_approved(
    background_tasks: BackgroundTasks, first_name: str, email: EmailStr, confirmed: bool
) -> None:
    content = (
        f"<p>Hi {first_name},</p>" "<p>Your Data to Science account has been approved. "
    )
    if confirmed:
        content += "You may now log in and start using Data to Science. "
    else:
        content += 'To start using Data to Science, please click <strong>"Confirm Email"</strong> in the separate confirmation email sent to your inbox. '
    content += (
        "If you have any questions, please reach out to support at "
        f"{settings.MAIL_FROM}.</p><br /><br />"
        "<p>-Data to Science Support</p>"
    )

    send_email(
        subject="Your Data to Science account has been approved",
        recipients=[email],
        body=content,
        background_tasks=background_tasks,
    )


def send_contact_email(
    background_tasks: BackgroundTasks,
    topic: str,
    subject: str,
    message: str,
    sender: Optional[Dict[str, Any]] = None,
) -> None:
    if sender:
        content = f"<p>Message sent from Data to Science user {sender['name']} ({sender['email']}):</p>"
    else:
        content = f"<p>Message from anonymous Data to Science user:</p>"

    api_domain = settings.API_DOMAIN

    content += f"<p>Topic:</p><blockquote>{topic}</blockquote>"
    content += f"<p>Subject:</p><blockquote>{subject}</blockquote>"
    content += f"<p>Message:</p><blockquote>{message}</blockquote>"

    content += "<br /><br /><p>-Data to Science Support</p>"

    send_email(
        subject=f"Data to Science Contact Form: {topic} ({api_domain})",
        recipients=[settings.MAIL_FROM],
        body=content,
        background_tasks=background_tasks,
    )
