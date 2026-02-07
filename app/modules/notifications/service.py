from app.modules.notifications.schemas import NotificationRequest


def send_notification(payload: NotificationRequest) -> dict:
    return {"status": "queued", "channel": payload.channel}
