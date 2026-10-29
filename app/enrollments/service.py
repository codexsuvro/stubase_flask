from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.enrollments.repository import (
    create_enrollment as save_enrollment,
    get_enrollment_by_unique_fields,
)


class StudentNotFoundError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass


class InvalidEnrollmentError(Exception):
    pass


class DuplicateEnrollmentError(Exception):
    pass


def create_enrollment(data):
    student_id = data["student_id"]
    course_id = data["course_id"]
    semester = data["semester"]
    academic_year = data["academic_year"].strip()
    status = data.get("status", "ENROLLED")

    # 1. Verify that the student exists.
    student = db.session.get(Student, student_id)

    if student is None:
        raise StudentNotFoundError("Student not found.")

    # 2. Verify that the course exists.
    course = db.session.get(Course, course_id)

    if course is None:
        raise CourseNotFoundError("Course not found.")

    # 3. Student and course must belong to the same department.
    if student.department_id != course.department_id:
        raise InvalidEnrollmentError(
            "Student and course must belong to the same department."
        )

    # 4. Enrollment semester must match the course semester.
    if semester != course.semester:
        raise InvalidEnrollmentError(
            f"Enrollment semester must match the course semester "
            f"({course.semester})."
        )

    # 5. Check for an existing enrollment.
    existing = get_enrollment_by_unique_fields(
        student_id=student_id,
        course_id=course_id,
        academic_year=academic_year,
        semester=semester,
    )

    if existing is not None:
        raise DuplicateEnrollmentError(
            "Student is already enrolled in this course "
            "for the specified academic year and semester."
        )

    enrollment = Enrollment(
        student_id=student.id,
        course_id=course.id,
        semester=semester,
        academic_year=academic_year,
        status=status,
    )

    try:
        return save_enrollment(enrollment)

    except IntegrityError as exc:
        db.session.rollback()

        # Handles a duplicate created concurrently by another request.
        existing = get_enrollment_by_unique_fields(
            student_id=student_id,
            course_id=course_id,
            academic_year=academic_year,
            semester=semester,
        )

        if existing is not None:
            raise DuplicateEnrollmentError(
                "Student is already enrolled in this course "
                "for the specified academic year and semester."
            ) from exc

        raise

    except Exception:
        db.session.rollback()
        raise