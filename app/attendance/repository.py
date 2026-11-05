from sqlalchemy import select, func
from app.extensions import db
from app.models.attendance import Attendance
from app.models.attendance_audit import AttendanceAudit
from app.models.enrollment import Enrollment
from app.models.course import Course


def get_attendance_by_id(attendance_id):
    return db.session.get(Attendance, attendance_id)


def get_attendance_by_enrollment_and_date(
    enrollment_id,
    attendance_date,
):
    statement = select(Attendance).where(
        Attendance.enrollment_id == enrollment_id,
        Attendance.attendance_date == attendance_date,
    )

    return db.session.scalar(statement)


def list_attendance():
    statement = select(Attendance).order_by(
        Attendance.attendance_date.desc(),
        Attendance.created_at.desc(),
    )

    return db.session.scalars(statement).all()


def list_attendance_by_enrollment(enrollment_id):
    statement = (
        select(Attendance)
        .where(Attendance.enrollment_id == enrollment_id)
        .order_by(Attendance.attendance_date.desc())
    )

    return db.session.scalars(statement).all()


def get_attendance_counts(enrollment_id):
    statement = (
        select(
            Attendance.status,
            func.count(Attendance.id),
        )
        .where(Attendance.enrollment_id == enrollment_id)
        .group_by(Attendance.status)
    )

    return db.session.execute(statement).all()


def create_attendance(attendance):
    db.session.add(attendance)
    db.session.commit()
    db.session.refresh(attendance)
    return attendance


def list_attendance_audits(attendance_id):
    statement = (
        select(AttendanceAudit)
        .where(AttendanceAudit.attendance_id == attendance_id)
        .order_by(AttendanceAudit.created_at.desc())
    )

    return db.session.scalars(statement).all()


def save_attendance_update(attendance, audit):
    db.session.add(audit)
    db.session.add(attendance)
    db.session.commit()
    db.session.refresh(attendance)

    return attendance


def list_attendance_paginated(
    page=1,
    per_page=10,
    student_id=None,
    status=None,
    course_code=None,
    start_date=None,
    end_date=None,
):
    """
    Return paginated attendance records with optional filters.
    """

    statement = (
        select(Attendance)
        .join(Attendance.enrollment)
        .join(Enrollment.course)
    )

    # Apply common filters
    if student_id is not None:
        statement = statement.where(
            Enrollment.student_id == student_id
        )

    if status is not None:
        statement = statement.where(
            Attendance.status == status
        )

    if course_code is not None:
        statement = statement.where(
            Course.course_code == course_code
        )

    if start_date is not None:
        statement = statement.where(
            Attendance.attendance_date >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Attendance.attendance_date <= end_date
        )

    # Count matching records before pagination
    count_statement = select(
        func.count()
    ).select_from(
        statement.order_by(None).subquery()
    )

    total_records = db.session.scalar(count_statement) or 0

    # Fetch paginated records
    records = db.session.scalars(
        statement
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.created_at.desc(),
            Attendance.id.desc(),
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