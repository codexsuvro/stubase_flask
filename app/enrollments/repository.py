from sqlalchemy import select
from app.extensions import db
from app.models.enrollment import Enrollment


def get_enrollment_by_id(enrollment_id):
    return db.session.get(Enrollment, enrollment_id)


def get_enrollment_by_unique_fields(
    student_id,
    course_id,
    academic_year,
    semester,
):
    statement = select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id,
        Enrollment.academic_year == academic_year,
        Enrollment.semester == semester,
    )

    return db.session.scalar(statement)


def list_enrollments():
    statement = select(Enrollment).order_by(
        Enrollment.academic_year.desc(),
        Enrollment.semester.asc(),
        Enrollment.created_at.desc(),
    )

    return db.session.scalars(statement).all()


def list_enrollments_by_student(student_id):
    statement = (
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .order_by(
            Enrollment.academic_year.desc(),
            Enrollment.semester.asc(),
        )
    )

    return db.session.scalars(statement).all()


def create_enrollment(enrollment):
    db.session.add(enrollment)
    db.session.commit()
    db.session.refresh(enrollment)
    return enrollment