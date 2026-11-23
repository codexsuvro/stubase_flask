from sqlalchemy import func, select

from app.extensions import db
from app.announcements.models import Announcement


def get_announcement_by_id(announcement_id, for_update=False):
    statement = select(Announcement).where(
        Announcement.id == announcement_id
    )

    if for_update:
        statement = statement.with_for_update()

    return db.session.scalar(statement)


def list_announcements(statement, page=1, per_page=20):
    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    items = db.session.scalars(
        statement
        .order_by(
            Announcement.created_at.desc(),
            Announcement.id.desc(),
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
