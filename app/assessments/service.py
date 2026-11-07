from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.faculty import Faculty
from app.assessments.repository import (
    get_assessment_by_id,
    get_assessment_by_unique_fields,
    create_assessment as save_assessment,
    update_assessment as save_assessment_changes,
    list_assessments_paginated,
)


class AssessmentNotFoundError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass


class InvalidAssessmentError(Exception):
    pass


class DuplicateAssessmentError(Exception):
    pass


class AssessmentAccessDeniedError(Exception):
    pass


def validate_course_access(course, actor_user_id, actor_role):
    """
    ADMIN can access every course.
    FACULTY can access only their assigned courses.
    """

    if actor_role == "ADMIN":
        return

    if actor_role != "FACULTY":
        raise AssessmentAccessDeniedError(
            "You are not authorized to manage assessments."
        )

    faculty = db.session.scalar(
        db.select(Faculty).where(
            Faculty.user_id == actor_user_id
        )
    )

    if faculty is None or faculty.id != course.faculty_id:
        raise AssessmentAccessDeniedError(
            "You can manage assessments only for your assigned courses."
        )


def validate_assessment_course(course, semester):
    if semester != course.semester:
        raise InvalidAssessmentError(
            f"Assessment semester must match the course semester "
            f"({course.semester})."
        )


def validate_assessment_marks(max_marks, passing_marks):
    if max_marks <= 0:
        raise InvalidAssessmentError(
            "Maximum marks must be greater than zero."
        )

    if passing_marks < 0:
        raise InvalidAssessmentError(
            "Passing marks cannot be negative."
        )

    if passing_marks > max_marks:
        raise InvalidAssessmentError(
            "Passing marks cannot exceed maximum marks."
        )


def check_duplicate_assessment(
    course_id,
    academic_year,
    semester,
    assessment_type,
    sequence_number,
    exclude_assessment_id=None,
):
    existing = get_assessment_by_unique_fields(
        course_id=course_id,
        academic_year=academic_year,
        semester=semester,
        assessment_type=assessment_type,
        sequence_number=sequence_number,
        exclude_assessment_id=exclude_assessment_id,
    )

    if existing is not None:
        raise DuplicateAssessmentError(
            "An assessment with the same course, academic year, "
            "semester, type and sequence number already exists."
        )


def create_assessment(data, actor_user_id, actor_role):
    course = db.session.get(Course, data["course_id"])

    if course is None:
        raise CourseNotFoundError("Course not found.")

    validate_course_access(
        course,
        actor_user_id,
        actor_role,
    )

    validate_assessment_course(
        course,
        data["semester"],
    )

    validate_assessment_marks(
        data["max_marks"],
        data["passing_marks"],
    )

    academic_year = data["academic_year"].strip()

    check_duplicate_assessment(
        course_id=course.id,
        academic_year=academic_year,
        semester=data["semester"],
        assessment_type=data["assessment_type"],
        sequence_number=data.get("sequence_number", 1),
    )

    assessment = Assessment(
        assessment_name=data["assessment_name"].strip(),
        assessment_type=data["assessment_type"],
        sequence_number=data.get("sequence_number", 1),
        course_id=course.id,
        semester=data["semester"],
        academic_year=academic_year,
        max_marks=data["max_marks"],
        passing_marks=data["passing_marks"],
        assessment_date=data["assessment_date"],
        description=data.get("description"),
    )

    try:
        return save_assessment(assessment)

    except IntegrityError as exc:
        db.session.rollback()

        existing = get_assessment_by_unique_fields(
            course_id=course.id,
            academic_year=academic_year,
            semester=data["semester"],
            assessment_type=data["assessment_type"],
            sequence_number=data.get("sequence_number", 1),
        )

        if existing is not None:
            raise DuplicateAssessmentError(
                "This assessment already exists."
            ) from exc

        raise

    except Exception:
        db.session.rollback()
        raise


def update_assessment(
    assessment_id,
    data,
    actor_user_id,
    actor_role,
):
    if not data:
        raise InvalidAssessmentError(
            "At least one field must be provided for an update."
        )
    
    assessment = get_assessment_by_id(assessment_id)

    if assessment is None:
        raise AssessmentNotFoundError(
            "Assessment not found."
        )

    validate_course_access(
        assessment.course,
        actor_user_id,
        actor_role,
    )
    
    course_id = data.get("course_id", assessment.course_id)
    semester = data.get("semester", assessment.semester)

    course = db.session.get(Course, course_id)

    if course is None:
        raise CourseNotFoundError("Course not found.")

    validate_course_access(
        course,
        actor_user_id,
        actor_role,
    )

    validate_assessment_course(course, semester)

    max_marks = data.get("max_marks", assessment.max_marks)
    passing_marks = data.get(
        "passing_marks",
        assessment.passing_marks,
    )

    validate_assessment_marks(max_marks, passing_marks)

    academic_year = data.get(
        "academic_year",
        assessment.academic_year,
    ).strip()

    assessment_type = data.get(
        "assessment_type",
        assessment.assessment_type,
    )

    sequence_number = data.get(
        "sequence_number",
        assessment.sequence_number,
    )

    check_duplicate_assessment(
        course_id=course.id,
        academic_year=academic_year,
        semester=semester,
        assessment_type=assessment_type,
        sequence_number=sequence_number,
        exclude_assessment_id=assessment.id,
    )

    try:
        assessment.assessment_name = data.get(
            "assessment_name",
            assessment.assessment_name,
        ).strip()

        assessment.assessment_type = assessment_type
        assessment.sequence_number = sequence_number
        assessment.course_id = course.id
        assessment.semester = semester
        assessment.academic_year = academic_year
        assessment.max_marks = max_marks
        assessment.passing_marks = passing_marks
        assessment.assessment_date = data.get(
            "assessment_date",
            assessment.assessment_date,
        )

        if "description" in data:
            assessment.description = data["description"]

        save_assessment_changes()

        db.session.refresh(assessment)

        return assessment

    except IntegrityError as exc:
        db.session.rollback()

        raise DuplicateAssessmentError(
            "This assessment conflicts with an existing assessment."
        ) from exc

    except Exception:
        db.session.rollback()
        raise
    
    
def get_faculty_profile(actor_user_id):
    """Resolve the Faculty profile using the authenticated User UUID."""

    return db.session.scalar(
        db.select(Faculty).where(
            Faculty.user_id == actor_user_id
        )
    )


def list_assessments_for_user(
    actor_user_id,
    actor_role,
    page=1,
    per_page=10,
    course_id=None,
    assessment_type=None,
    academic_year=None,
    semester=None,
):
    """List assessments according to the authenticated user's role."""

    faculty_id = None

    if actor_role == "FACULTY":
        faculty = get_faculty_profile(actor_user_id)

        if faculty is None:
            raise AssessmentAccessDeniedError(
                "Faculty profile was not found."
            )

        faculty_id = faculty.id

    elif actor_role != "ADMIN":
        raise AssessmentAccessDeniedError(
            "You are not authorized to view assessments."
        )

    return list_assessments_paginated(
        page=page,
        per_page=per_page,
        course_id=course_id,
        assessment_type=assessment_type,
        academic_year=academic_year,
        semester=semester,
        faculty_id=faculty_id,
    )


def get_assessment_for_user(
    assessment_id,
    actor_user_id,
    actor_role,
):
    """Retrieve one assessment after checking course ownership."""

    assessment = get_assessment_by_id(assessment_id)

    if assessment is None:
        raise AssessmentNotFoundError(
            "Assessment was not found."
        )

    validate_course_access(
        assessment.course,
        actor_user_id,
        actor_role,
    )

    return assessment