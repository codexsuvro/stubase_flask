from sqlalchemy import select
from app.extensions import db
from app.models.course_prerequisite import CoursePrerequisite


def get_prerequisite(course_id, prerequisite_course_id):
    statement = select(CoursePrerequisite).where(
        CoursePrerequisite.course_id == course_id,
        CoursePrerequisite.prerequisite_course_id == prerequisite_course_id,
    )

    return db.session.scalar(statement)


def list_prerequisites(course_id):
    statement = (
        select(CoursePrerequisite)
        .where(CoursePrerequisite.course_id == course_id)
        .order_by(CoursePrerequisite.created_at.asc())
    )

    return db.session.scalars(statement).all()


def save_prerequisite(prerequisite):
    db.session.add(prerequisite)
    db.session.commit()
    db.session.refresh(prerequisite)
    return prerequisite


def delete_prerequisite(prerequisite):
    db.session.delete(prerequisite)
    db.session.commit()