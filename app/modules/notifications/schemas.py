from pydantic import BaseModel


class NotificationRequest(BaseModel):
    channel: str
    message: str
