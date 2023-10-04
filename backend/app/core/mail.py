from fastapi_mail import FastMail

from app.core.config import settings

conf = settings.MAIL_CONF
if conf:
    fm = FastMail(config=conf)
