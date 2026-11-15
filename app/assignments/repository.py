from sqlalchemy import select, func

from app.extensions import db
from app.assignments.models import Assignment, AssignmentSubmission
from app.models.course_offering import CourseOffering
from app.models.enrollment import Enrollment


def get_assignment_by_id(assignment_id):
    return db.session.get(Assignment, assignment_id)


def get_submission_by_id(submission_id):
    return db.session.get(AssignmentSubmission, submission_id)


def get_submission_by_assignment_student(assignment_id, student_id):
    statement = select(AssignmentSubmission).where(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == student_id,
    )

    return db.session.scalar(statement)


def list_assignments_paginated(
    page=1,
    per_page=10,
    offering_id=None,
    status=None,
    faculty_id=None,
):
    statement = select(Assignment)

    if faculty_id is not None:
        statement = (
            statement
            .join(Assignment.offering)
            .where(CourseOffering.faculty_id == faculty_id)
        )

    if offering_id is not None:
        statement = statement.where(
            Assignment.offering_id == offering_id
        )

    if status is not None:
        statement = statement.where(
            Assignment.status == status
        )

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    items = db.session.scalars(
        statement
        .order_by(
            Assignment.created_at.desc(),
            Assignment.id.asc(),
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


def list_student_assignments_paginated(
    student_id,
    page=1,
    per_page=10,
    offering_id=None,
    status="PUBLISHED",
):
    statement = (
        select(Assignment)
        .join(
            Enrollment,
            Enrollment.offering_id == Assignment.offering_id,
        )
        .where(
            Enrollment.student_id == student_id,
            Enrollment.status == "ENROLLED",
            Assignment.status == status,
        )
    )

    if offering_id is not None:
        statement = statement.where(
            Assignment.offering_id == offering_id
        )

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    items = db.session.scalars(
        statement
        .order_by(
            Assignment.due_at.asc(),
            Assignment.created_at.desc(),
        )
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).unique().all()

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


def list_submissions_paginated(
    assignment_id,
    page=1,
    per_page=10,
    status=None,
):
    statement = select(AssignmentSubmission).where(
        AssignmentSubmission.assignment_id == assignment_id
    )

    if status is not None:
        statement = statement.where(
            AssignmentSubmission.status == status
        )

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    items = db.session.scalars(
        statement
        .order_by(
            AssignmentSubmission.submitted_at.desc(),
            AssignmentSubmission.id.asc(),
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


def save_assignment(assignment):
    db.session.add(assignment)
    db.session.commit()
    db.session.refresh(assignment)
    return assignment


def save_submission(submission):
    db.session.add(submission)
    db.session.commit()
    db.session.refresh(submission)
    return submission


def commit_changes():
    db.session.commit()
