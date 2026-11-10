from sqlalchemy import select
from app.extensions import db
from app.models.course_offering import CourseOffering


def get_offering_by_id(offering_id):
    return db.session.get(CourseOffering, offering_id)


def get_offering_by_unique_key(course_id, semester_id, section_code):
    statement = select(CourseOffering).where(
        CourseOffering.course_id == course_id,
        CourseOffering.semester_id == semester_id,
        CourseOffering.section_code == section_code,
    )
    return db.session.scalar(statement)


def list_offerings(semester_id=None, course_id=None, faculty_id=None, status=None):
    statement = select(CourseOffering).order_by(CourseOffering.created_at.desc())
    if semester_id is not None:
        statement = statement.where(CourseOffering.semester_id == semester_id)
    if course_id is not None:
        statement = statement.where(CourseOffering.course_id == course_id)
    if faculty_id is not None:
        statement = statement.where(CourseOffering.faculty_id == faculty_id)
    if status is not None:
        statement = statement.where(CourseOffering.status == status)
    return db.session.scalars(statement).all()
