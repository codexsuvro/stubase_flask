from datetime import date
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.faculty import Faculty
from app.models.enrollment import Enrollment
from app.models.attendance import Attendance
from app.models.attendance_audit import AttendanceAudit
from app.attendance.repository import (
    create_attendance as save_attendance,
    get_attendance_by_id,
    get_attendance_by_enrollment_and_date,
    get_attendance_counts,
    list_attendance_by_enrollment,
    list_attendance_audits,
    save_attendance_update,
)
from app.models.student import Student


class EnrollmentNotFoundError(Exception):
    pass


class DuplicateAttendanceError(Exception):
    pass


class AttendanceNotFoundError(Exception):
    pass


class AttendancePermissionError(Exception):
    pass


def ensure_enrollment_access(enrollment, user_id):
    """
    ADMIN can access every enrollment.
    FACULTY can access only enrollments belonging to their assigned courses.
    """

    user = db.session.get(User, UUID(str(user_id)))

    if user is None:
        raise AttendancePermissionError("Authenticated user was not found.")

    role_name = (
        user.role.role_name.strip().upper()
        if user.role and user.role.role_name
        else None
    )

    if role_name == "ADMIN":
        return

    if role_name != "FACULTY":
        raise AttendancePermissionError(
            "You do not have permission to access this attendance."
        )

    faculty_statement = select(Faculty).where(
        Faculty.user_id == user.id
    )
    faculty = db.session.scalar(faculty_statement)

    if faculty is None:
        raise AttendancePermissionError(
            "Faculty profile was not found for this account."
        )

    if enrollment.course.faculty_id != faculty.id:
        raise AttendancePermissionError(
            "You can only access attendance for your assigned courses."
        )

def get_student_profile_for_user(user_id):
    """
    Resolve the Student profile belonging to the authenticated user.
    """

    user = db.session.get(User, UUID(str(user_id)))

    if user is None:
        raise AttendancePermissionError(
            "Authenticated user was not found."
        )

    role_name = (
        user.role.role_name.strip().upper()
        if user.role and user.role.role_name
        else None
    )

    if role_name != "STUDENT":
        raise AttendancePermissionError(
            "Only students can access this resource."
        )

    student_statement = select(Student).where(
        Student.user_id == user.id
    )

    student = db.session.scalar(student_statement)

    if student is None:
        raise AttendancePermissionError(
            "Student profile was not found for this account."
        )

    return student


def get_student_attendance(user_id):
    """
    Return attendance records for all enrollments of the logged-in student.
    """

    student = get_student_profile_for_user(user_id)

    statement = (
        select(Attendance)
        .join(Enrollment)
        .where(Enrollment.student_id == student.id)
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.created_at.desc(),
        )
    )

    return db.session.scalars(statement).all()


def get_student_attendance_summary(user_id):
    """
    Return attendance summary grouped by the student's enrollments.
    """

    student = get_student_profile_for_user(user_id)

    statement = (
        select(Enrollment)
        .where(Enrollment.student_id == student.id)
        .order_by(Enrollment.created_at.desc())
    )

    enrollments = db.session.scalars(statement).all()

    summaries = []

    for enrollment in enrollments:
        summary = calculate_attendance_summary(enrollment.id)

        summary["course_code"] = enrollment.course.course_code
        summary["course_name"] = enrollment.course.course_name
        summary["academic_year"] = enrollment.academic_year

        summaries.append(summary)

    return summaries


def get_student_attendance_shortage(
    user_id,
    minimum_percentage=75.0,
):
    """
    Return attendance shortage information for all student enrollments.
    """

    student = get_student_profile_for_user(user_id)

    statement = (
        select(Enrollment)
        .where(Enrollment.student_id == student.id)
        .order_by(Enrollment.created_at.desc())
    )

    enrollments = db.session.scalars(statement).all()

    results = []

    for enrollment in enrollments:
        summary = calculate_attendance_summary(enrollment.id)
        percentage = summary["attendance_percentage"]

        results.append({
            "enrollment_id": enrollment.id,
            "course_code": enrollment.course.course_code,
            "course_name": enrollment.course.course_name,
            "attendance_percentage": percentage,
            "minimum_required_percentage": minimum_percentage,
            "shortage_detected": (
                summary["total_classes"] > 0
                and percentage < minimum_percentage
            ),
            "total_classes": summary["total_classes"],
        })

    return results


def ensure_attendance_access(attendance, user_id):
    ensure_enrollment_access(attendance.enrollment, user_id)


def create_attendance(data, user_id):
    enrollment_id = data["enrollment_id"]
    attendance_date = data.get("attendance_date") or date.today()
    status = data["status"]
    remarks = data.get("remarks")

    enrollment = db.session.get(Enrollment, enrollment_id)

    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    if enrollment.status != "ENROLLED":
        raise EnrollmentNotFoundError(
            "Attendance cannot be recorded for an enrollment "
            "that is not active."
        )

    ensure_enrollment_access(enrollment, user_id)

    existing = get_attendance_by_enrollment_and_date(
        enrollment_id,
        attendance_date,
    )

    if existing is not None:
        raise DuplicateAttendanceError(
            "Attendance has already been recorded for this "
            "enrollment on the specified date."
        )

    attendance = Attendance(
        enrollment_id=enrollment_id,
        attendance_date=attendance_date,
        status=status,
        remarks=remarks,
    )

    try:
        return save_attendance(attendance)

    except IntegrityError as exc:
        db.session.rollback()

        existing = get_attendance_by_enrollment_and_date(
            enrollment_id,
            attendance_date,
        )

        if existing is not None:
            raise DuplicateAttendanceError(
                "Attendance has already been recorded for this "
                "enrollment on the specified date."
            ) from exc

        raise

    except Exception:
        db.session.rollback()
        raise


def get_attendance_for_user(attendance_id, user_id):
    attendance = get_attendance_by_id(attendance_id)

    if attendance is None:
        raise AttendanceNotFoundError("Attendance record not found.")

    ensure_attendance_access(attendance, user_id)
    return attendance


def get_enrollment_attendance_for_user(enrollment_id, user_id):
    enrollment = db.session.get(Enrollment, enrollment_id)

    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    ensure_enrollment_access(enrollment, user_id)
    return list_attendance_by_enrollment(enrollment_id)


def calculate_attendance_summary(enrollment_id):
    counts = get_attendance_counts(enrollment_id)

    status_counts = {
        status: count
        for status, count in counts
    }

    present_count = status_counts.get("PRESENT", 0)
    absent_count = status_counts.get("ABSENT", 0)
    late_count = status_counts.get("LATE", 0)

    total_classes = present_count + absent_count + late_count

    attendance_percentage = (
        ((present_count + late_count) / total_classes) * 100
        if total_classes > 0
        else 0.0
    )

    return {
        "enrollment_id": enrollment_id,
        "total_classes": total_classes,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "attendance_percentage": round(attendance_percentage, 2),
    }


def get_attendance_summary_for_user(enrollment_id, user_id):
    enrollment = db.session.get(Enrollment, enrollment_id)

    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    ensure_enrollment_access(enrollment, user_id)
    return calculate_attendance_summary(enrollment_id)


def update_attendance(attendance_id, data, changed_by_user_id):
    attendance = db.session.get(Attendance, attendance_id)

    if attendance is None:
        raise AttendanceNotFoundError("Attendance record not found.")

    ensure_attendance_access(attendance, changed_by_user_id)

    previous_status = attendance.status
    previous_remarks = attendance.remarks

    new_status = data.get("status", previous_status)
    new_remarks = data.get("remarks", previous_remarks)

    if (
        previous_status == new_status
        and previous_remarks == new_remarks
    ):
        return attendance

    audit = AttendanceAudit(
        attendance_id=attendance.id,
        changed_by_user_id=UUID(str(changed_by_user_id)),
        previous_status=previous_status,
        new_status=new_status,
        previous_remarks=previous_remarks,
        new_remarks=new_remarks,
    )

    attendance.status = new_status
    attendance.remarks = new_remarks

    try:
        return save_attendance_update(attendance, audit)

    except Exception:
        db.session.rollback()
        raise


def get_attendance_history(attendance_id, user_id):
    attendance = db.session.get(Attendance, attendance_id)

    if attendance is None:
        raise AttendanceNotFoundError("Attendance record not found.")

    ensure_attendance_access(attendance, user_id)
    return list_attendance_audits(attendance_id)


def get_attendance_shortage(
    enrollment_id,
    user_id,
    minimum_percentage=75.0,
):
    enrollment = db.session.get(Enrollment, enrollment_id)

    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    ensure_enrollment_access(enrollment, user_id)

    summary = calculate_attendance_summary(enrollment_id)
    percentage = summary["attendance_percentage"]

    return {
        "enrollment_id": enrollment_id,
        "attendance_percentage": percentage,
        "minimum_required_percentage": minimum_percentage,
        "shortage_detected": (
            summary["total_classes"] > 0
            and percentage < minimum_percentage
        ),
        "total_classes": summary["total_classes"],
    }
