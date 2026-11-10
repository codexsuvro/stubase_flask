from sqlalchemy import select, func
from app.extensions import db
from app.models.assessment import Assessment
from app.models.course_offering import CourseOffering


def get_assessment_by_id(assessment_id):

    return db.session.get(
        Assessment,
        assessment_id,
    )


def get_assessment_by_offering_unique_fields(
    offering_id,
    assessment_type,
    sequence_number,
    exclude_assessment_id=None,
):

    statement = select(Assessment).where(
        Assessment.offering_id == offering_id,
        Assessment.assessment_type == assessment_type,
        Assessment.sequence_number == sequence_number,
    )

    if exclude_assessment_id is not None:
        statement = statement.where(
            Assessment.id != exclude_assessment_id
        )

    return db.session.scalar(statement)


def list_assessments_paginated(
    page=1,
    per_page=10,
    offering_id=None,
    course_id=None,
    assessment_type=None,
    academic_year=None,
    semester=None,
    faculty_id=None,
):

    statement = select(Assessment)

    if faculty_id is not None:
        statement = (
            statement
            .join(
                Assessment.offering
            )
            .where(
                CourseOffering.faculty_id == faculty_id
            )
        )

    if offering_id is not None:
        statement = statement.where(
            Assessment.offering_id == offering_id
        )

    if course_id is not None:
        statement = statement.where(
            Assessment.course_id == course_id
        )

    if assessment_type is not None:
        statement = statement.where(
            Assessment.assessment_type == assessment_type
        )

    if academic_year is not None:
        statement = statement.where(
            Assessment.academic_year == academic_year
        )

    if semester is not None:
        statement = statement.where(
            Assessment.semester == semester
        )

    count_statement = (
        select(func.count())
        .select_from(
            statement.order_by(None).subquery()
        )
    )

    total_records = (
        db.session.scalar(count_statement) or 0
    )

    records = db.session.scalars(
        statement
        .order_by(
            Assessment.academic_year.desc(),
            Assessment.semester.asc(),
            Assessment.assessment_date.desc(),
            Assessment.assessment_type.asc(),
            Assessment.sequence_number.asc(),
            Assessment.id.asc(),
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


def create_assessment(assessment):

    db.session.add(assessment)
    db.session.commit()
    db.session.refresh(assessment)

    return assessment


def update_assessment():

    db.session.commit()

    return True


def delete_assessment(assessment):

    db.session.delete(assessment)
    db.session.commit()

    return True