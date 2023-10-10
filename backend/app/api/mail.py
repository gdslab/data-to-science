from fastapi import BackgroundTasks
from pydantic import EmailStr

from app.api.deps import send_email
from app.core.config import settings


def send_email_confirmation(
    background_tasks: BackgroundTasks,
    first_name: str,
    email: EmailStr,
    confirmation_token: str,
):
    confirmation_url = settings.DOMAIN + settings.API_V1_STR + "/auth/confirm-email?"
    confirmation_url += f"token={confirmation_token}"

    confirmation_btn = "<button style='display: inline-block;outline: none;"
    confirmation_btn += "border-radius: 3px;font-size: 14px;"
    confirmation_btn += "font-weight: 500;line-height: 16px;padding: 2px 16px;"
    confirmation_btn += "height: 38px;min-width: 96px;min-height: 38px;border: none;"
    confirmation_btn += "color: #fff;background-color: rgb(88, 101, 242);'>"
    confirmation_btn += "Confirm Email</button>"

    content = f"<p>Hi {first_name},</p>"
    content += (
        "<p>Thank you for creating an account at D2S. Please click the below button "
        "to confirm your email address.<br /><br />"
        f"<a href='{confirmation_url}' target='_blank'>{confirmation_btn}</a>"
        "<br /><br />"
        "The confirmation button will expire in 1 hour. If you do not respond within 1 "
        "hour, you will need to request a new confirmation email.<br /><br />"
        "If you have any questions, please reach out to support at "
        f"{settings.MAIL_FROM}.</p>"
        "<p>-D2S Support</p>"
    )

    send_email(
        subject="Confirm your email address",
        recipient=email,
        body=content,
        background_tasks=background_tasks,
    )


def send_password_recovery(
    background_tasks: BackgroundTasks,
    first_name: str,
    email: EmailStr,
    recovery_token: str,
):
    recover_url = settings.DOMAIN + "/auth/resetpassword?"
    recover_url += f"token={recovery_token}"

    recover_btn = "<button style='display: inline-block;outline: none;"
    recover_btn += "border-radius: 3px;font-size: 14px;"
    recover_btn += "font-weight: 500;line-height: 16px;padding: 2px 16px;"
    recover_btn += "height: 38px;min-width: 96px;min-height: 38px;border: none;"
    recover_btn += "color: #fff;background-color: rgb(88, 101, 242);'>"
    recover_btn += "Reset Password</button>"

    content = f"<p>Hi {first_name},</p>"
    content += (
        "<p>Someone requested a password reset for your D2S account. To reset your "
        "password, please click the below button.<br /><br />"
        f"<a href='{recover_url}' target='_blank'>{recover_btn}</a>"
        "<br /><br />"
        "After clicking the button, you will be taken to a page where you can reset "
        "your password. If you do not respond within 1 hour, you will need to request "
        "a new password reset email. If you did not make this request, you may "
        "ignore this email.<br /><br />"
        "If you have any questions, please reach out to support at "
        f"{settings.MAIL_FROM}.</p>"
        "<p>-D2S Support</p>"
    )

    send_email(
        subject="D2S Password Reset",
        recipient=email,
        body=content,
        background_tasks=background_tasks,
    )
