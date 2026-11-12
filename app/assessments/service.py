from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.assessment import Assessment
from app.models.course_offering import CourseOffering
from app.models.faculty import Faculty
from app.assessments.repository import (
    get_assessment_by_id,
    get_assessment_by_offering_unique_fields,
    create_assessment as save_assessment,
    update_assessment as save_assessment_changes,
    list_assessments_paginated,
)


class AssessmentNotFoundError(Exception):
    pass


class CourseNotFoundError(Exception):
    pass


class OfferingNotFoundError(Exception):
    pass


class InvalidAssessmentError(Exception):
    pass


class DuplicateAssessmentError(Exception):
    pass


class AssessmentAccessDeniedError(Exception):
    pass


def get_faculty_profile(actor_user_id):
    """Resolve the Faculty profile using the authenticated User UUID."""

    return db.session.scalar(
        select(Faculty).where(
            Faculty.user_id == actor_user_id
        )
    )


def validate_offering_access(
    offering,
    actor_user_id,
    actor_role,
):
    """
    ADMIN can manage every offering.
    FACULTY can manage only offerings assigned to them.
    """

    if actor_role == "ADMIN":
        return

    if actor_role != "FACULTY":
        raise AssessmentAccessDeniedError(
            "You are not authorized to manage assessments."
        )

    faculty = get_faculty_profile(actor_user_id)

    if faculty is None or faculty.id != offering.faculty_id:
        raise AssessmentAccessDeniedError(
            "You can manage assessments only for your assigned offerings."
        )


def get_offering_or_raise(offering_id):

    offering = db.session.get(
        CourseOffering,
        offering_id,
    )

    if offering is None:
        raise OfferingNotFoundError(
            "Course offering not found."
        )

    return offering


def validate_offering_academic_state(offering):

    semester = offering.semester

    if semester is None:
        raise InvalidAssessmentError(
            "The offering is not associated with a valid semester."
        )

    academic_year = semester.academic_year

    if academic_year is None:
        raise InvalidAssessmentError(
            "The semester is not associated with a valid academic year."
        )

    if offering.status != "OPEN":
        raise InvalidAssessmentError(
            "Assessments can be created or updated only for OPEN offerings."
        )

    if semester.status != "ACTIVE":
        raise InvalidAssessmentError(
            "Assessments can be created or updated only in an ACTIVE semester."
        )

    if academic_year.status != "ACTIVE":
        raise InvalidAssessmentError(
            "Assessments can be created or updated only in an ACTIVE academic year."
        )

    return semester, academic_year


def validate_assessment_date(assessment_date, semester):

    if not (
        semester.start_date
        <= assessment_date
        <= semester.end_date
    ):
        raise InvalidAssessmentError(
            "Assessment date must fall within the semester start and end dates."
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
    offering_id,
    assessment_type,
    sequence_number,
    exclude_assessment_id=None,
):

    existing = get_assessment_by_offering_unique_fields(
        offering_id=offering_id,
        assessment_type=assessment_type,
        sequence_number=sequence_number,
        exclude_assessment_id=exclude_assessment_id,
    )

    if existing is not None:
        raise DuplicateAssessmentError(
            "An assessment with the same offering, type and sequence number already exists."
        )


def create_assessment(data, actor_user_id, actor_role):

    offering = get_offering_or_raise(
        data["offering_id"]
    )

    validate_offering_access(
        offering,
        actor_user_id,
        actor_role,
    )

    semester, academic_year = validate_offering_academic_state(
        offering
    )

    validate_assessment_date(
        data["assessment_date"],
        semester,
    )

    validate_assessment_marks(
        data["max_marks"],
        data["passing_marks"],
    )

    sequence_number = data.get("sequence_number", 1)

    check_duplicate_assessment(
        offering_id=offering.id,
        assessment_type=data["assessment_type"],
        sequence_number=sequence_number,
    )

    assessment = Assessment(
        assessment_name=data["assessment_name"].strip(),
        assessment_type=data["assessment_type"],
        sequence_number=sequence_number,

        # Legacy compatibility fields are derived from Offering.
        course_id=offering.course_id,
        semester=semester.semester_number,
        academic_year=academic_year.name,

        offering_id=offering.id,

        max_marks=data["max_marks"],
        passing_marks=data["passing_marks"],
        weightage=data["weightage"],
        assessment_date=data["assessment_date"],
        description=data.get("description"),
    )

    try:
        return save_assessment(assessment)

    except IntegrityError as exc:
        db.session.rollback()

        existing = get_assessment_by_offering_unique_fields(
            offering_id=offering.id,
            assessment_type=data["assessment_type"],
            sequence_number=sequence_number,
        )

        if existing is not None:
            raise DuplicateAssessmentError(
                "An assessment with the same offering, type and sequence number already exists."
            ) from exc

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

    assessment = get_assessment_by_id(
        assessment_id
    )

    if assessment is None:
        raise AssessmentNotFoundError(
            "Assessment not found."
        )

    # Legacy assessments without an offering are not editable
    # through the new offering-based workflow.
    if assessment.offering_id is None:
        raise InvalidAssessmentError(
            "This is a legacy assessment without a course offering and cannot be updated through the offering-based API."
        )

    offering = assessment.offering

    validate_offering_access(
        offering,
        actor_user_id,
        actor_role,
    )

    semester, academic_year = validate_offering_academic_state(
        offering
    )

    max_marks = data.get(
        "max_marks",
        assessment.max_marks,
    )

    passing_marks = data.get(
        "passing_marks",
        assessment.passing_marks,
    )

    assessment_date = data.get(
        "assessment_date",
        assessment.assessment_date,
    )

    assessment_type = data.get(
        "assessment_type",
        assessment.assessment_type,
    )

    sequence_number = data.get(
        "sequence_number",
        assessment.sequence_number,
    )

    validate_assessment_marks(
        max_marks,
        passing_marks,
    )

    validate_assessment_date(
        assessment_date,
        semester,
    )

    check_duplicate_assessment(
        offering_id=offering.id,
        assessment_type=assessment_type,
        sequence_number=sequence_number,
        exclude_assessment_id=assessment.id,
    )

    try:
        if "assessment_name" in data:
            assessment.assessment_name = (
                data["assessment_name"].strip()
            )

        assessment.assessment_type = assessment_type
        assessment.sequence_number = sequence_number
        assessment.max_marks = max_marks
        assessment.passing_marks = passing_marks
        assessment.assessment_date = assessment_date

        if "description" in data:
            assessment.description = data["description"]

        # Keep compatibility fields aligned with the offering.
        assessment.course_id = offering.course_id
        assessment.semester = semester.semester_number
        assessment.academic_year = academic_year.name

        save_assessment_changes()

        db.session.refresh(assessment)

        return assessment

    except IntegrityError as exc:
        db.session.rollback()

        existing = get_assessment_by_offering_unique_fields(
            offering_id=offering.id,
            assessment_type=assessment_type,
            sequence_number=sequence_number,
            exclude_assessment_id=assessment.id,
        )

        if existing is not None:
            raise DuplicateAssessmentError(
                "This assessment conflicts with an existing assessment."
            ) from exc

        raise


def list_assessments_for_user(
    actor_user_id,
    actor_role,
    page=1,
    per_page=10,
    offering_id=None,
    course_id=None,
    assessment_type=None,
    academic_year=None,
    semester=None,
):

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
        offering_id=offering_id,
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

    assessment = get_assessment_by_id(
        assessment_id
    )

    if assessment is None:
        raise AssessmentNotFoundError(
            "Assessment was not found."
        )

    if assessment.offering_id is None:

        if actor_role == "ADMIN":
            return assessment

        raise AssessmentAccessDeniedError(
            "Legacy assessments without a course offering are not accessible through faculty offering-based authorization."
        )

    validate_offering_access(
        assessment.offering,
        actor_user_id,
        actor_role,
    )

    return assessment