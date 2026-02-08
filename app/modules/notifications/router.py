from fastapi import APIRouter, Depends

from app.models import User
from app.modules.auth.router import get_current_user
from app.modules.notifications.schemas import NotificationRequest
from app.modules.notifications.service import send_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/send")
def send(
    payload: NotificationRequest,
    current_user: User = Depends(get_current_user),
):
    return send_notification(payload)
