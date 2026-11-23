from datetime import UTC, datetime
from uuid import UUID

from app.extensions import db
from app.notifications.models import Notification, NotificationDelivery
from app.notifications.repository import (
    count_unread_notifications,
    get_notification_for_user,
    list_notifications_for_user,
    mark_all_notifications_read,
)


class NotificationError(Exception):
    pass


class NotificationNotFoundError(NotificationError):
    pass


class NotificationValidationError(NotificationError):
    pass


def _now():
    return datetime.now(UTC)


def build_notification(
    recipient,
    notification_type,
    title,
    message,
    announcement_id=None,
    queue_email=False,
    created_at=None,
):
    if not recipient.is_active:
        raise NotificationValidationError(
            "Inactive users cannot receive notifications."
        )
    if (
        not isinstance(notification_type, str)
        or not notification_type.strip()
        or len(notification_type) > 50
        or not isinstance(title, str)
        or len(title) > 200
        or not title.strip()
        or "\r" in title
        or "\n" in title
        or not isinstance(message, str)
        or len(message) > 10000
        or not message.strip()
    ):
        raise NotificationValidationError(
            "Notification type, title, and message must be valid."
        )

    created_at = created_at or _now()
    notification = Notification(
        recipient=recipient,
        announcement_id=announcement_id,
        notification_type=notification_type.strip(),
        title=title.strip(),
        message=message.strip(),
        created_at=created_at,
    )
    if queue_email and recipient.is_verified:
        notification.deliveries.append(
            NotificationDelivery(
                channel="EMAIL",
                status="PENDING",
                next_attempt_at=created_at,
            )
        )
    return notification


def _normalize_user_id(user_id):
    if isinstance(user_id, UUID):
        return user_id
    try:
        return UUID(str(user_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotificationNotFoundError(
            "Authenticated user was not found."
        ) from exc


def list_my_notifications(
    recipient_id,
    page=1,
    per_page=20,
    unread_only=False,
):
    recipient_id = _normalize_user_id(recipient_id)
    return list_notifications_for_user(
        recipient_id,
        page=page,
        per_page=per_page,
        unread_only=unread_only,
    )


def get_my_unread_notification_count(recipient_id):
    recipient_id = _normalize_user_id(recipient_id)
    return {"unread_count": count_unread_notifications(recipient_id)}


def mark_notification_read(notification_id, recipient_id):
    recipient_id = _normalize_user_id(recipient_id)
    notification = get_notification_for_user(
        notification_id,
        recipient_id,
    )
    if notification is None:
        raise NotificationNotFoundError("Notification not found.")

    if notification.read_at is None:
        notification.read_at = _now()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return notification


def mark_all_my_notifications_read(recipient_id):
    recipient_id = _normalize_user_id(recipient_id)
    now = _now()
    try:
        updated_count = mark_all_notifications_read(
            recipient_id,
            now,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {"updated_count": updated_count}
