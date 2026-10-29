from sqlalchemy import select
from app.extensions import db
from app.models.course import Course


def get_course_by_code(course_code):
    statement = select(Course).where(
        Course.course_code == course_code
    )
    return db.session.scalar(statement)


def get_course_by_id(course_id):
    return db.session.get(Course, course_id)


def list_courses():
    statement = select(Course).order_by(Course.course_code.asc())
    return db.session.scalars(statement).all()


def create_course(course):
    db.session.add(course)
    db.session.commit()
    db.session.refresh(course)
    return course
