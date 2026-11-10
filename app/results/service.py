from decimal import Decimal, InvalidOperation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.results.repository import (
    create_result as save_result,
    get_result_by_id,
    get_result_by_assessment_and_enrollment,
    update_result as save_result_changes,
    list_results_paginated,
    get_student_analytics,
    get_course_analytics,
    get_assessment_analytics,
)


class AssessmentResultNotFoundError(Exception):
    pass


class AssessmentNotFoundError(Exception):
    pass


class EnrollmentNotFoundError(Exception):
    pass


class InvalidAssessmentResultError(Exception):
    pass


class DuplicateAssessmentResultError(Exception):
    pass


class AssessmentResultAccessDeniedError(Exception):
    pass


def get_faculty_profile(actor_user_id):
    return db.session.scalar(
        select(Faculty).where(Faculty.user_id == actor_user_id)
    )


def get_student_profile(actor_user_id):
    return db.session.scalar(
        select(Student).where(Student.user_id == actor_user_id)
    )


def validate_offering_access(offering, actor_user_id, actor_role):
    if actor_role == "ADMIN":
        return

    if actor_role != "FACULTY":
        raise AssessmentResultAccessDeniedError(
            "You are not authorized to manage assessment results."
        )

    faculty = get_faculty_profile(actor_user_id)
    if faculty is None or faculty.id != offering.faculty_id:
        raise AssessmentResultAccessDeniedError(
            "You can manage results only for your assigned offerings."
        )


def validate_course_offering_access(course_id, actor_user_id, actor_role):
    if actor_role == "ADMIN":
        return

    if actor_role != "FACULTY":
        raise AssessmentResultAccessDeniedError(
            "You are not authorized to view course analytics."
        )

    faculty = get_faculty_profile(actor_user_id)
    if faculty is None:
        raise AssessmentResultAccessDeniedError("Faculty profile was not found.")

    assigned_offering_id = db.session.scalar(
        select(CourseOffering.id).where(
            CourseOffering.course_id == course_id,
            CourseOffering.faculty_id == faculty.id,
        ).limit(1)
    )
    if assigned_offering_id is None:
        raise AssessmentResultAccessDeniedError(
            "You can view analytics only for courses with your assigned offerings."
        )


def validate_assessment_enrollment(assessment, enrollment):
    if assessment.offering_id is None:
        raise InvalidAssessmentResultError(
            "Legacy assessment cannot be used with new offering-based enrollment."
        )

    if enrollment.offering_id is None:
        raise InvalidAssessmentResultError(
            "Legacy enrollment cannot be used with new offering-based assessment."
        )

    if assessment.offering_id != enrollment.offering_id:
        raise InvalidAssessmentResultError(
            "Assessment and enrollment must belong to the same course offering."
        )

    if enrollment.status != "ENROLLED":
        raise InvalidAssessmentResultError(
            "Results can only be recorded for enrolled students."
        )


def validate_marks(marks_obtained, max_marks):
    try:
        marks = Decimal(str(marks_obtained))
        maximum = Decimal(str(max_marks))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InvalidAssessmentResultError("Invalid marks value.") from exc

    if not marks.is_finite():
        raise InvalidAssessmentResultError("Marks must be a finite number.")
    if marks < 0:
        raise InvalidAssessmentResultError("Marks cannot be negative.")
    if marks > maximum:
        raise InvalidAssessmentResultError(
            f"Marks cannot exceed maximum marks ({maximum})."
        )
    return marks


def _validate_result_association_and_access(assessment, enrollment, actor_user_id, actor_role):
    if assessment.offering is None:
        raise InvalidAssessmentResultError("Legacy assessment has no course offering.")

    validate_offering_access(assessment.offering, actor_user_id, actor_role)
    validate_assessment_enrollment(assessment, enrollment)


def create_result(data, actor_user_id, actor_role):
    assessment = db.session.get(Assessment, data["assessment_id"])
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    enrollment = db.session.get(Enrollment, data["enrollment_id"])
    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    _validate_result_association_and_access(
        assessment, enrollment, actor_user_id, actor_role
    )

    marks = validate_marks(data["marks_obtained"], assessment.max_marks)
    existing = get_result_by_assessment_and_enrollment(assessment.id, enrollment.id)
    if existing is not None:
        raise DuplicateAssessmentResultError(
            "A result already exists for this assessment and enrollment."
        )

    result_data = {
        "assessment_id": assessment.id,
        "enrollment_id": enrollment.id,
        "marks_obtained": marks,
        "remarks": data.get("remarks"),
        "graded_by": actor_user_id,
    }

    try:
        result = save_result(result_data)
        db.session.commit()
        return get_result_by_id(result.id)
    except IntegrityError as exc:
        db.session.rollback()
        raise DuplicateAssessmentResultError(
            "A result already exists for this assessment and enrollment."
        ) from exc
    except Exception:
        db.session.rollback()
        raise


def update_result(result_id, data, actor_user_id, actor_role):
    if not data:
        raise InvalidAssessmentResultError(
            "At least one field must be provided for an update."
        )

    result = get_result_by_id(result_id)
    if result is None:
        raise AssessmentResultNotFoundError("Assessment result not found.")

    _validate_result_association_and_access(
        result.assessment,
        result.enrollment,
        actor_user_id,
        actor_role,
    )

    marks = validate_marks(
        data.get("marks_obtained", result.marks_obtained),
        result.assessment.max_marks,
    )
    update_data = {"marks_obtained": marks}
    if "remarks" in data:
        update_data["remarks"] = data["remarks"]

    try:
        save_result_changes(result, update_data)
        db.session.commit()
        return get_result_by_id(result.id)
    except Exception:
        db.session.rollback()
        raise


def get_result_for_user(result_id, actor_user_id, actor_role):
    result = get_result_by_id(result_id)
    if result is None:
        raise AssessmentResultNotFoundError("Assessment result not found.")

    _validate_result_association_and_access(
        result.assessment,
        result.enrollment,
        actor_user_id,
        actor_role,
    )
    return result


def list_results_for_user(
    actor_user_id,
    actor_role,
    page=1,
    per_page=10,
    assessment_id=None,
    enrollment_id=None,
    course_id=None,
):
    faculty_id = None
    if actor_role == "FACULTY":
        faculty = get_faculty_profile(actor_user_id)
        if faculty is None:
            raise AssessmentResultAccessDeniedError("Faculty profile was not found.")
        faculty_id = faculty.id
    elif actor_role != "ADMIN":
        raise AssessmentResultAccessDeniedError(
            "You are not authorized to view assessment results."
        )

    return list_results_paginated(
        page=page,
        per_page=per_page,
        assessment_id=assessment_id,
        enrollment_id=enrollment_id,
        course_id=course_id,
        faculty_id=faculty_id,
    )


def list_my_results(actor_user_id, page=1, per_page=10, assessment_id=None):
    student = get_student_profile(actor_user_id)
    if student is None:
        raise AssessmentResultAccessDeniedError("Student profile was not found.")

    return list_results_paginated(
        page=page,
        per_page=per_page,
        assessment_id=assessment_id,
        student_id=student.id,
    )


def format_analytics(data):
    total = data["total_results"] if "total_results" in data else data["total_assessments"]
    total_marks = Decimal(str(data["total_marks_obtained"] or 0))
    total_max = Decimal(str(data.get("total_max_marks", 0) or 0))
    percentage = (total_marks / total_max) * Decimal("100") if total_max > 0 else Decimal("0")

    return {
        "total_assessments": total,
        "total_students": data.get("total_students", 1 if total else 0),
        "total_marks_obtained": total_marks.quantize(Decimal("0.01")),
        "total_max_marks": total_max.quantize(Decimal("0.01")),
        "percentage": percentage.quantize(Decimal("0.01")),
        "average_marks": Decimal(str(data["average_marks"] or 0)).quantize(Decimal("0.01")),
        "highest_marks": Decimal(str(data["highest_marks"] or 0)).quantize(Decimal("0.01")),
        "lowest_marks": Decimal(str(data["lowest_marks"] or 0)).quantize(Decimal("0.01")),
        "passed": data["passed"] or 0,
        "failed": data["failed"] or 0,
    }


def get_my_result_analytics(actor_user_id):
    student = get_student_profile(actor_user_id)
    if student is None:
        raise AssessmentResultAccessDeniedError("Student profile was not found.")
    return format_analytics(get_student_analytics(student.id))


def get_course_result_analytics(course_id, actor_user_id, actor_role):
    course = db.session.get(Course, course_id)
    if course is None:
        raise AssessmentNotFoundError("Course not found.")

    validate_course_offering_access(course_id, actor_user_id, actor_role)
    return format_analytics(get_course_analytics(course_id))


def get_assessment_result_analytics(assessment_id, actor_user_id, actor_role):
    assessment = db.session.get(Assessment, assessment_id)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    if assessment.offering is None:
        raise InvalidAssessmentResultError("Legacy assessment has no course offering.")

    validate_offering_access(assessment.offering, actor_user_id, actor_role)
    return format_analytics(get_assessment_analytics(assessment_id))
