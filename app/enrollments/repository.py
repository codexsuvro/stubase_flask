from sqlalchemy import select, func
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


def list_enrollments_paginated(
    page=1,
    per_page=10,
    student_id=None,
    course_id=None,
    academic_year=None,
    semester=None,
    status=None,
):
    """
    Return paginated enrollment records with optional filters.
    """

    statement = select(Enrollment)

    # Apply filters
    if student_id is not None:
        statement = statement.where(
            Enrollment.student_id == student_id
        )

    if course_id is not None:
        statement = statement.where(
            Enrollment.course_id == course_id
        )

    if academic_year is not None:
        statement = statement.where(
            Enrollment.academic_year == academic_year
        )

    if semester is not None:
        statement = statement.where(
            Enrollment.semester == semester
        )

    if status is not None:
        statement = statement.where(
            Enrollment.status == status
        )

    # Count matching records before pagination
    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )

    total_records = db.session.scalar(count_statement) or 0

    # Fetch paginated records
    records = db.session.scalars(
        statement
        .order_by(
            Enrollment.academic_year.desc(),
            Enrollment.semester.asc(),
            Enrollment.created_at.desc(),
            Enrollment.id.desc(),
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
        "items": records,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
    }


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