from fastapi import APIRouter

from app.modules.notifications.schemas import NotificationRequest
from app.modules.notifications.service import send_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/send")
def send(payload: NotificationRequest):
    return send_notification(payload)
