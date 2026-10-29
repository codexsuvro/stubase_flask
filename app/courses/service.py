from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.course import Course
from app.models.department import Department
from app.models.faculty import Faculty

from app.courses.repository import (
    create_course as save_course,
    get_course_by_code,
)


class CourseAlreadyExistsError(Exception):
    pass


class DepartmentNotFoundError(Exception):
    pass


class FacultyNotFoundError(Exception):
    pass


class InvalidCourseAssignmentError(Exception):
    pass


def create_course(data):
    course_code = data["course_code"].strip().upper()

    if get_course_by_code(course_code) is not None:
        raise CourseAlreadyExistsError(
            f"Course code '{course_code}' already exists."
        )

    department = db.session.get(
        Department,
        data["department_id"],
    )

    if department is None:
        raise DepartmentNotFoundError(
            "Department not found."
        )

    faculty_statement = select(Faculty).where(
        Faculty.user_id == data["faculty_user_id"]
    )
    faculty = db.session.scalar(faculty_statement)

    if faculty is None:
        raise FacultyNotFoundError(
            "No Faculty profile exists for this User account."
        )

    if faculty.department_id != department.id:
        raise InvalidCourseAssignmentError(
            "The assigned Faculty must belong to the course's department."
        )

    course = Course(
        course_code=course_code,
        course_name=data["course_name"].strip(),
        credits=data["credits"],
        semester=data["semester"],
        department_id=department.id,
        faculty_id=faculty.id,
    )

    try:
        return save_course(course)
    except IntegrityError:
        db.session.rollback()

        # Handles a concurrent request creating the same course code.
        if get_course_by_code(course_code) is not None:
            raise CourseAlreadyExistsError(
                f"Course code '{course_code}' already exists."
            )

        raise
    except Exception:
        db.session.rollback()
        raise
