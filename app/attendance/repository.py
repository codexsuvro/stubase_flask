from sqlalchemy import select, func
from app.extensions import db
from app.models.attendance import Attendance
from app.models.attendance_audit import AttendanceAudit


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