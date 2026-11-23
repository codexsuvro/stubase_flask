from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError

from app.announcements.models import Announcement
from app.announcements.repository import (
    get_announcement_by_id,
    list_announcements,
)
from app.extensions import db
from app.models.course_offering import CourseOffering
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.user import User
from app.notifications.service import build_notification


class AnnouncementError(Exception):
    pass


class AnnouncementNotFoundError(AnnouncementError):
    pass


class AnnouncementForbiddenError(AnnouncementError):
    pass


class AnnouncementConflictError(AnnouncementError):
    pass


class AnnouncementValidationError(AnnouncementError):
    pass


def _now():
    return datetime.now(UTC)


def _normalize_user_id(user_id):
    if isinstance(user_id, UUID):
        return user_id
    try:
        return UUID(str(user_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise AnnouncementNotFoundError(
            "Authenticated user was not found."
        ) from exc


def _get_actor(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise AnnouncementNotFoundError("User profile not found.")
    if user.role is None:
        raise AnnouncementForbiddenError(
            "The authenticated user has no assigned role."
        )
    return user, user.role.role_name.strip().upper()


def _get_offering(offering_id):
    offering = db.session.get(CourseOffering, offering_id)
    if offering is None:
        raise AnnouncementNotFoundError("Course offering not found.")
    return offering


def _require_offering_manager(offering, user_id, role):
    if role == "ADMIN":
        return
    if role != "FACULTY":
        raise AnnouncementForbiddenError(
            "You are not authorized to manage announcements."
        )
    if offering.faculty.user_id != user_id:
        raise AnnouncementForbiddenError(
            "Faculty may manage announcements only for their assigned offerings."
        )


def _require_announcement_manager(announcement, user_id, role):
    if role == "ADMIN":
        return
    if role != "FACULTY" or announcement.audience_type != "COURSE":
        raise AnnouncementForbiddenError(
            "You are not authorized to manage this announcement."
        )
    if announcement.created_by != user_id:
        raise AnnouncementForbiddenError(
            "You may manage only announcements that you created."
        )
    _require_offering_manager(
        announcement.offering,
        user_id,
        role,
    )


def create_announcement(data, actor_user_id):
    actor_user_id = _normalize_user_id(actor_user_id)
    _, actor_role = _get_actor(actor_user_id)
    audience_type = data["audience_type"]
    offering = None

    if audience_type == "GLOBAL":
        if data.get("offering_id") is not None:
            raise AnnouncementValidationError(
                "Global announcements cannot target a course offering."
            )
        if actor_role != "ADMIN":
            raise AnnouncementForbiddenError(
                "Only administrators can create global announcements."
            )
    elif audience_type == "COURSE":
        if data.get("offering_id") is None:
            raise AnnouncementValidationError(
                "Course announcements require a course offering."
            )
        offering = _get_offering(data["offering_id"])
        _require_offering_manager(offering, actor_user_id, actor_role)
    else:
        raise AnnouncementValidationError(
            "Unsupported announcement audience."
        )

    announcement = Announcement(
        audience_type=audience_type,
        offering=offering,
        created_by=actor_user_id,
        title=data["title"].strip(),
        body=data["body"].strip(),
        status="DRAFT",
    )

    try:
        db.session.add(announcement)
        db.session.commit()
        db.session.refresh(announcement)
    except Exception:
        db.session.rollback()
        raise

    return announcement


def _announcement_list_statement(user_id, role):
    statement = select(Announcement)

    if role == "ADMIN":
        return statement

    if role == "FACULTY":
        managed_offerings = (
            select(CourseOffering.id)
            .join(Faculty, Faculty.id == CourseOffering.faculty_id)
            .where(Faculty.user_id == user_id)
        )
        return statement.where(
            or_(
                and_(
                    Announcement.audience_type == "GLOBAL",
                    Announcement.status == "PUBLISHED",
                ),
                and_(
                    Announcement.offering_id.in_(managed_offerings),
                    or_(
                        Announcement.status == "PUBLISHED",
                        Announcement.created_by == user_id,
                    ),
                ),
            )
        )

    enrolled_offerings = (
        select(Enrollment.offering_id)
        .join(Student, Student.id == Enrollment.student_id)
        .where(
            Student.user_id == user_id,
            Enrollment.status == "ENROLLED",
            Enrollment.offering_id.is_not(None),
        )
    )
    return statement.where(
        Announcement.status == "PUBLISHED",
        or_(
            Announcement.audience_type == "GLOBAL",
            Announcement.offering_id.in_(enrolled_offerings),
        ),
    )


def list_announcements_for_user(
    user_id,
    page=1,
    per_page=20,
    status=None,
):
    user_id = _normalize_user_id(user_id)
    _, role = _get_actor(user_id)
    statement = _announcement_list_statement(user_id, role)

    if status is not None:
        statement = statement.where(Announcement.status == status)

    return list_announcements(
        statement,
        page=page,
        per_page=per_page,
    )


def _user_can_view(announcement, user_id, role):
    if role == "ADMIN":
        return True

    if announcement.status != "PUBLISHED":
        if role == "FACULTY" and announcement.created_by == user_id:
            return (
                announcement.audience_type == "COURSE"
                and announcement.offering.faculty.user_id == user_id
            )
        return False

    if announcement.audience_type == "GLOBAL":
        return True

    if role == "FACULTY":
        return announcement.offering.faculty.user_id == user_id

    statement = select(Enrollment.id).join(
        Student,
        Student.id == Enrollment.student_id,
    ).where(
        Student.user_id == user_id,
        Enrollment.offering_id == announcement.offering_id,
        Enrollment.status == "ENROLLED",
    ).limit(1)
    return db.session.scalar(statement) is not None


def get_announcement_for_user(announcement_id, user_id):
    user_id = _normalize_user_id(user_id)
    announcement = get_announcement_by_id(announcement_id)
    if announcement is None:
        raise AnnouncementNotFoundError("Announcement not found.")

    _, role = _get_actor(user_id)
    if not _user_can_view(announcement, user_id, role):
        raise AnnouncementNotFoundError("Announcement not found.")
    return announcement


def update_announcement(announcement_id, data, actor_user_id):
    actor_user_id = _normalize_user_id(actor_user_id)
    _, actor_role = _get_actor(actor_user_id)
    announcement = get_announcement_by_id(
        announcement_id,
        for_update=True,
    )
    if announcement is None:
        raise AnnouncementNotFoundError("Announcement not found.")

    _require_announcement_manager(
        announcement,
        actor_user_id,
        actor_role,
    )
    if announcement.status != "DRAFT":
        raise AnnouncementConflictError(
            "Only draft announcements can be edited."
        )

    for field in ("title", "body"):
        if field in data:
            setattr(announcement, field, data[field].strip())

    try:
        db.session.commit()
        db.session.refresh(announcement)
    except Exception:
        db.session.rollback()
        raise
    return announcement


def _get_announcement_recipients(announcement):
    if announcement.audience_type == "GLOBAL":
        statement = select(User).where(User.is_active.is_(True))
    else:
        statement = (
            select(User)
            .join(Student, Student.user_id == User.id)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .where(
                Enrollment.offering_id == announcement.offering_id,
                Enrollment.status == "ENROLLED",
                User.is_active.is_(True),
            )
            .distinct()
        )

    return db.session.scalars(statement).all()


def publish_announcement(announcement_id, actor_user_id):
    actor_user_id = _normalize_user_id(actor_user_id)
    _, actor_role = _get_actor(actor_user_id)
    announcement = get_announcement_by_id(
        announcement_id,
        for_update=True,
    )
    if announcement is None:
        raise AnnouncementNotFoundError("Announcement not found.")

    _require_announcement_manager(
        announcement,
        actor_user_id,
        actor_role,
    )
    if announcement.status != "DRAFT":
        raise AnnouncementConflictError(
            "Only draft announcements can be published."
        )

    now = _now()
    recipients = _get_announcement_recipients(announcement)
    announcement.status = "PUBLISHED"
    announcement.published_at = now

    for recipient in recipients:
        if recipient.id == actor_user_id:
            continue

        notification = build_notification(
            recipient=recipient,
            announcement_id=announcement.id,
            notification_type="ANNOUNCEMENT",
            title=announcement.title,
            message=announcement.body,
            queue_email=True,
            created_at=now,
        )
        db.session.add(notification)

    try:
        db.session.commit()
        db.session.refresh(announcement)
    except IntegrityError as exc:
        db.session.rollback()
        raise AnnouncementConflictError(
            "The announcement was published concurrently. Refresh and retry."
        ) from exc
    except Exception:
        db.session.rollback()
        raise

    return announcement


def archive_announcement(announcement_id, actor_user_id):
    actor_user_id = _normalize_user_id(actor_user_id)
    _, actor_role = _get_actor(actor_user_id)
    announcement = get_announcement_by_id(
        announcement_id,
        for_update=True,
    )
    if announcement is None:
        raise AnnouncementNotFoundError("Announcement not found.")

    _require_announcement_manager(
        announcement,
        actor_user_id,
        actor_role,
    )
    if announcement.status == "ARCHIVED":
        return announcement

    announcement.status = "ARCHIVED"
    announcement.archived_at = _now()
    try:
        db.session.commit()
        db.session.refresh(announcement)
    except Exception:
        db.session.rollback()
        raise
    return announcement
