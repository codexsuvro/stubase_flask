from sqlalchemy import select
from app.extensions import db
from app.models.course_waitlist import CourseWaitlist


def get_waitlist_entry(student_id, offering_id):

    statement = select(CourseWaitlist).where(
        CourseWaitlist.student_id == student_id,
        CourseWaitlist.offering_id == offering_id,
    )

    return db.session.scalar(statement)


def get_waitlist_by_id(waitlist_id):

    return db.session.get(
        CourseWaitlist,
        waitlist_id,
    )


def list_waitlist_entries(offering_id=None, student_id=None):

    statement = select(CourseWaitlist)

    if offering_id is not None:
        statement = statement.where(
            CourseWaitlist.offering_id == offering_id
        )

    if student_id is not None:
        statement = statement.where(
            CourseWaitlist.student_id == student_id
        )

    statement = statement.order_by(
        CourseWaitlist.created_at.asc(),
        CourseWaitlist.id.asc(),
    )

    return db.session.scalars(statement).all()