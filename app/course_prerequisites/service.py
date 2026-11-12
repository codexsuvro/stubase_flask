from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.course import Course
from app.models.course_prerequisite import CoursePrerequisite
from app.models.enrollment import Enrollment
from app.course_prerequisites.repository import (
    get_prerequisite,
    list_prerequisites,
    save_prerequisite,
    delete_prerequisite,
)


class CoursePrerequisiteNotFoundError(Exception):
    pass


class CoursePrerequisiteConflictError(Exception):
    pass


class InvalidCoursePrerequisiteError(Exception):
    pass


def _get_course(course_id):
    course = db.session.get(Course, course_id)

    if course is None:
        raise CoursePrerequisiteNotFoundError(
            "Course not found."
        )

    return course


def _would_create_cycle(course_id, prerequisite_course_id):
    """
    Check whether adding course_id -> prerequisite_course_id
    would create a circular prerequisite dependency.
    """

    visited = set()
    stack = [prerequisite_course_id]

    while stack:
        current_id = stack.pop()

        if current_id == course_id:
            return True

        if current_id in visited:
            continue

        visited.add(current_id)

        statement = select(
            CoursePrerequisite.prerequisite_course_id
        ).where(
            CoursePrerequisite.course_id == current_id
        )

        dependencies = db.session.scalars(statement).all()
        stack.extend(dependencies)

    return False


def create_prerequisite(course_id, prerequisite_course_id):

    course = _get_course(course_id)
    prerequisite_course = _get_course(prerequisite_course_id)

    if course.id == prerequisite_course.id:
        raise InvalidCoursePrerequisiteError(
            "A course cannot be its own prerequisite."
        )

    if course.department_id != prerequisite_course.department_id:
        raise InvalidCoursePrerequisiteError(
            "Prerequisite course must belong to the same department."
        )

    existing = get_prerequisite(
        course.id,
        prerequisite_course.id,
    )

    if existing:
        raise CoursePrerequisiteConflictError(
            "This prerequisite is already configured."
        )

    if _would_create_cycle(course.id, prerequisite_course.id):
        raise InvalidCoursePrerequisiteError(
            "Circular prerequisite dependency is not allowed."
        )

    prerequisite = CoursePrerequisite(
        course_id=course.id,
        prerequisite_course_id=prerequisite_course.id,
    )

    try:
        return save_prerequisite(prerequisite)

    except IntegrityError as exc:
        db.session.rollback()
        raise CoursePrerequisiteConflictError(
            "Prerequisite conflicts with an existing record."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def get_course_prerequisites(course_id):
    _get_course(course_id)
    return list_prerequisites(course_id)


def remove_prerequisite(course_id, prerequisite_course_id):

    _get_course(course_id)
    _get_course(prerequisite_course_id)

    prerequisite = get_prerequisite(
        course_id,
        prerequisite_course_id,
    )

    if prerequisite is None:
        raise CoursePrerequisiteNotFoundError(
            "Course prerequisite not found."
        )

    delete_prerequisite(prerequisite)

    return {
        "message": "Course prerequisite removed successfully."
    }


def validate_student_prerequisites(student_id, course_id):

    prerequisites = list_prerequisites(course_id)

    for prerequisite in prerequisites:

        completed_enrollment = db.session.scalar(
            select(Enrollment.id).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == prerequisite.prerequisite_course_id,
                Enrollment.status == "COMPLETED",
            ).limit(1)
        )

        if completed_enrollment is None:

            raise InvalidCoursePrerequisiteError(
                "Student has not completed prerequisite course "
                f"{prerequisite.prerequisite_course.course_code}."
            )

    return True