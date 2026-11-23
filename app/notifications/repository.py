from sqlalchemy import func, select, update

from app.extensions import db
from app.notifications.models import Notification


def get_notification_for_user(notification_id, recipient_id):
    statement = select(Notification).where(
        Notification.id == notification_id,
        Notification.recipient_id == recipient_id,
    )
    return db.session.scalar(statement)


def list_notifications_for_user(
    recipient_id,
    page=1,
    per_page=20,
    unread_only=False,
):
    statement = select(Notification).where(
        Notification.recipient_id == recipient_id
    )

    if unread_only:
        statement = statement.where(Notification.read_at.is_(None))

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    items = db.session.scalars(
        statement
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()

    total_pages = (
        (total_records + per_page - 1) // per_page
        if total_records
        else 0
    )

    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
    }


def count_unread_notifications(recipient_id):
    statement = select(func.count(Notification.id)).where(
        Notification.recipient_id == recipient_id,
        Notification.read_at.is_(None),
    )
    return db.session.scalar(statement) or 0


def mark_all_notifications_read(recipient_id, read_at):
    statement = (
        update(Notification)
        .where(
            Notification.recipient_id == recipient_id,
            Notification.read_at.is_(None),
        )
        .values(
            read_at=read_at,
            updated_at=read_at,
        )
    )
    result = db.session.execute(statement)
    return result.rowcount or 0
