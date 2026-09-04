from apps.notifications.models import Notification, NotificationType


def create_notification(
    *,
    merchant_id: int,
    recipient_type: str,
    recipient_name: str = "",
    order=None,
    message: str = "",
    type: str = NotificationType.SYSTEM,
) -> Notification:
    return Notification.objects.create(
        merchant_id=merchant_id,
        recipient_type=recipient_type,
        recipient_name=recipient_name,
        order=order,
        message=message,
        type=type,
    )