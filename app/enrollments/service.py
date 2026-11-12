from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.course_offering import CourseOffering
from app.enrollments.repository import (
    create_enrollment as save_enrollment,
    get_enrollment_by_unique_fields,
)
from app.course_prerequisites.service import (
    validate_student_prerequisites,
    InvalidCoursePrerequisiteError,
)


class StudentNotFoundError(Exception):
    pass


class OfferingNotFoundError(Exception):
    pass


class InvalidEnrollmentError(Exception):
    pass


class DuplicateEnrollmentError(Exception):
    pass


def create_enrollment(data):

    student = db.session.get(
        Student,
        data["student_id"],
    )

    if student is None:
        raise StudentNotFoundError(
            "Student not found."
        )

    # Lock the offering row before validating capacity.
    offering = db.session.scalar(
        select(CourseOffering)
        .where(CourseOffering.id == data["offering_id"])
        .with_for_update()
    )
    if offering is None:
        raise OfferingNotFoundError(
            "Course offering not found."
        )

    if offering.status != "OPEN":
        raise InvalidEnrollmentError(
            "Students can enroll only in OPEN course offerings."
        )

    semester = offering.semester
    academic_year = semester.academic_year

    if semester.status != "ACTIVE":
        raise InvalidEnrollmentError(
            "Enrollment requires an ACTIVE semester."
        )

    if academic_year.status != "ACTIVE":
        raise InvalidEnrollmentError(
            "Enrollment requires an ACTIVE academic year."
        )

    if student.department_id != offering.course.department_id:
        raise InvalidEnrollmentError(
            "Student and course must belong to the same department."
        )

    existing = get_enrollment_by_unique_fields(
        student.id,
        offering.id,
    )

    if existing is not None:
        raise DuplicateEnrollmentError(
            "Student is already enrolled in this course offering."
        )

    # Validate all configured course prerequisites.
    try:
        validate_student_prerequisites(
            student.id,
            offering.course_id,
        )

    except InvalidCoursePrerequisiteError as exc:
        raise InvalidEnrollmentError(str(exc)) from exc

    enrollment_count = db.session.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.offering_id == offering.id,
            Enrollment.status == "ENROLLED",
        )
    ) or 0

    if enrollment_count >= offering.capacity:
        raise InvalidEnrollmentError(
            "Course offering has reached its enrollment capacity. "
            "Student may join the waitlist."
        )

    enrollment = Enrollment(
        student_id=student.id,
        course_id=offering.course_id,
        offering_id=offering.id,
        academic_year=academic_year.name,
        semester=semester.semester_number,
        status="ENROLLED",
    )

    try:
        return save_enrollment(enrollment)
    except IntegrityError as exc:
        db.session.rollback()

        existing = get_enrollment_by_unique_fields(
            student.id,
            offering.id,
        )

        if existing is not None:
            raise DuplicateEnrollmentError(
                "Student is already enrolled in this course offering."
            ) from exc
        raise
    except Exception:
        db.session.rollback()
        raise