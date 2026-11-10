from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.course import Course
from app.models.semester import Semester
from app.models.faculty import Faculty
from app.models.enrollment import Enrollment
from app.models.course_offering import CourseOffering
from app.course_offerings.repository import (
    get_offering_by_id, get_offering_by_unique_key, list_offerings,
)

VALID_STATUSES = {"DRAFT", "OPEN", "CLOSED", "CANCELLED"}


class CourseOfferingNotFoundError(Exception): pass
class CourseNotFoundError(Exception): pass
class SemesterNotFoundError(Exception): pass
class FacultyNotFoundError(Exception): pass
class CourseOfferingConflictError(Exception): pass
class InvalidCourseOfferingError(Exception): pass


def _get_related(data):
    course = db.session.get(Course, data["course_id"])
    if course is None:
        raise CourseNotFoundError("Course not found.")
    semester = db.session.get(Semester, data["semester_id"])
    if semester is None:
        raise SemesterNotFoundError("Semester not found.")
    faculty = db.session.get(Faculty, data["faculty_id"])
    if faculty is None:
        raise FacultyNotFoundError("Faculty not found.")
    if faculty.department_id != course.department_id:
        raise InvalidCourseOfferingError(
            "Assigned Faculty must belong to the Course department."
        )
    if semester.status == "COMPLETED":
        raise InvalidCourseOfferingError(
            "Cannot create or modify an offering in a COMPLETED semester."
        )
    return course, semester, faculty


def create_offering(data):
    course, semester, faculty = _get_related(data)
    section = data["section_code"].strip().upper()
    status = data.get("status", "DRAFT")
    if not section:
        raise ValueError("Section code cannot be blank.")
    if status not in VALID_STATUSES:
        raise ValueError("Invalid course offering status.")
    if status == "OPEN" and semester.status != "ACTIVE":
        raise InvalidCourseOfferingError("An offering can be OPEN only in an ACTIVE semester.")
    if get_offering_by_unique_key(course.id, semester.id, section):
        raise CourseOfferingConflictError("This Course already has an offering with this section in the selected Semester.")
    offering = CourseOffering(
        course_id=course.id,
        semester_id=semester.id,
        faculty_id=faculty.id,
        section_code=section,
        capacity=data["capacity"],
        status=status,
    )
    try:
        db.session.add(offering)
        db.session.commit()
        return get_offering_by_id(offering.id)
    except IntegrityError as exc:
        db.session.rollback()
        raise CourseOfferingConflictError("Course offering conflicts with an existing record.") from exc
    except Exception:
        db.session.rollback()
        raise


def get_offering(offering_id):
    offering = get_offering_by_id(offering_id)
    if offering is None:
        raise CourseOfferingNotFoundError("Course offering not found.")
    return offering


def get_all_offerings(filters):
    return list_offerings(**filters)


def update_offering(offering_id, data):
    offering = get_offering(offering_id)
    if offering.status in {"CANCELLED", "CLOSED"}:
        raise InvalidCourseOfferingError("CLOSED or CANCELLED offerings cannot be modified.")
    if offering.semester.status == "COMPLETED":
        raise InvalidCourseOfferingError("Offerings in a COMPLETED semester cannot be modified.")
    faculty_id = data.get("faculty_id", offering.faculty_id)
    faculty = db.session.get(Faculty, faculty_id)
    if faculty is None:
        raise FacultyNotFoundError("Faculty not found.")
    if faculty.department_id != offering.course.department_id:
        raise InvalidCourseOfferingError("Assigned Faculty must belong to the Course department.")
    section = data.get("section_code", offering.section_code).strip().upper()
    existing = get_offering_by_unique_key(offering.course_id, offering.semester_id, section)
    if existing and existing.id != offering.id:
        raise CourseOfferingConflictError("This Course already has an offering with this section in the selected Semester.")
    new_capacity = data.get("capacity", offering.capacity)
    enrollment_count = db.session.query(Enrollment.id).filter(
        Enrollment.offering_id == offering.id,
        Enrollment.status == "ENROLLED",
    ).count()
    if new_capacity < enrollment_count:
        raise InvalidCourseOfferingError(
            "Capacity cannot be lower than the current enrolled student count."
        )
    offering.faculty_id = faculty.id
    offering.section_code = section
    offering.capacity = new_capacity
    try:
        db.session.commit()
        return offering
    except IntegrityError as exc:
        db.session.rollback()
        raise CourseOfferingConflictError("Course offering conflicts with an existing record.") from exc
    except Exception:
        db.session.rollback()
        raise


def update_offering_status(offering_id, status):
    offering = get_offering(offering_id)
    if status not in VALID_STATUSES:
        raise ValueError("Invalid course offering status.")
    if offering.status == "CANCELLED" and status != "CANCELLED":
        raise InvalidCourseOfferingError("A CANCELLED offering cannot be reopened.")
    if offering.status == "CLOSED" and status not in {"CLOSED", "CANCELLED"}:
        raise InvalidCourseOfferingError("A CLOSED offering cannot be reopened.")
    if status == "OPEN" and offering.semester.status != "ACTIVE":
        raise InvalidCourseOfferingError("An offering can be OPEN only in an ACTIVE semester.")
    if status == "OPEN" and offering.semester.academic_year.status != "ACTIVE":
        raise InvalidCourseOfferingError("The Academic Year must be ACTIVE before opening an offering.")
    if status in {"CLOSED", "CANCELLED"}:
        pass
    elif offering.semester.status == "COMPLETED":
        raise InvalidCourseOfferingError("An offering in a COMPLETED semester cannot be reopened.")
    offering.status = status
    try:
        db.session.commit()
        return offering
    except Exception:
        db.session.rollback()
        raise
