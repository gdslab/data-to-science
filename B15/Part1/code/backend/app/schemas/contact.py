from pydantic import BaseModel, Field


class ContactForm(BaseModel):
    topic: str
    subject: str = Field(min_length=5, max_length=60)
    message: str = Field(min_length=30, max_length=1000)
