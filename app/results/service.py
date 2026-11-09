from decimal import Decimal, InvalidOperation
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.student import Student
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
        db.select(Faculty).where(
            Faculty.user_id == actor_user_id
        )
    )


def get_student_profile(actor_user_id):

    return db.session.scalar(
        db.select(Student).where(
            Student.user_id == actor_user_id
        )
    )


def validate_course_access(
    course,
    actor_user_id,
    actor_role,
):

    if actor_role == "ADMIN":
        return

    if actor_role != "FACULTY":
        raise AssessmentResultAccessDeniedError(
            "You are not authorized to manage assessment results."
        )

    faculty = get_faculty_profile(actor_user_id)

    if faculty is None or faculty.id != course.faculty_id:
        raise AssessmentResultAccessDeniedError(
            "You can manage results only for your assigned courses."
        )


def validate_assessment_enrollment(
    assessment,
    enrollment,
):

    if assessment.course_id != enrollment.course_id:
        raise InvalidAssessmentResultError(
            "The assessment and enrollment must belong to the same course."
        )

    if enrollment.status != "ENROLLED":
        raise InvalidAssessmentResultError(
            "Results can only be recorded for enrolled students."
        )

    if assessment.semester != enrollment.semester:
        raise InvalidAssessmentResultError(
            "Assessment and enrollment semesters do not match."
        )

    if assessment.academic_year != enrollment.academic_year:
        raise InvalidAssessmentResultError(
            "Assessment and enrollment academic years do not match."
        )


def validate_marks(marks_obtained, max_marks):
    try:
        marks = Decimal(str(marks_obtained))
        maximum = Decimal(str(max_marks))
    except (InvalidOperation, TypeError, ValueError):
        raise InvalidAssessmentResultError(
            "Invalid marks value."
        )

    if not marks.is_finite():
        raise InvalidAssessmentResultError(
            "Marks must be a finite number."
        )

    if marks < 0:
        raise InvalidAssessmentResultError(
            "Marks cannot be negative."
        )

    if marks > maximum:
        raise InvalidAssessmentResultError(
            f"Marks cannot exceed maximum marks ({maximum})."
        )

    return marks


def create_result(
    data,
    actor_user_id,
    actor_role,
):

    assessment = db.session.get(
        Assessment,
        data["assessment_id"],
    )

    if assessment is None:
        raise AssessmentNotFoundError(
            "Assessment not found."
        )

    enrollment = db.session.get(
        Enrollment,
        data["enrollment_id"],
    )

    if enrollment is None:
        raise EnrollmentNotFoundError(
            "Enrollment not found."
        )

    validate_course_access(
        assessment.course,
        actor_user_id,
        actor_role,
    )

    validate_assessment_enrollment(
        assessment,
        enrollment,
    )

    marks = validate_marks(
        data["marks_obtained"],
        assessment.max_marks,
    )

    existing = get_result_by_assessment_and_enrollment(
        assessment.id,
        enrollment.id,
    )

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


def update_result(
    result_id,
    data,
    actor_user_id,
    actor_role,
):
    if not data:
        raise InvalidAssessmentResultError(
            "At least one field must be provided for an update."
        )

    result = get_result_by_id(result_id)

    if result is None:
        raise AssessmentResultNotFoundError(
            "Assessment result not found."
        )

    validate_course_access(
        result.assessment.course,
        actor_user_id,
        actor_role,
    )

    updated_marks = data.get(
        "marks_obtained",
        result.marks_obtained,
    )

    marks = validate_marks(
        updated_marks,
        result.assessment.max_marks,
    )

    update_data = {
        "marks_obtained": marks,
    }

    if "remarks" in data:
        update_data["remarks"] = data["remarks"]

    try:
        save_result_changes(result, update_data)
        db.session.commit()

        return get_result_by_id(result.id)

    except Exception:
        db.session.rollback()
        raise


def get_result_for_user(
    result_id,
    actor_user_id,
    actor_role,
):
    result = get_result_by_id(result_id)

    if result is None:
        raise AssessmentResultNotFoundError(
            "Assessment result not found."
        )

    validate_course_access(
        result.assessment.course,
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
            raise AssessmentResultAccessDeniedError(
                "Faculty profile was not found."
            )

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


def list_my_results(
    actor_user_id,
    page=1,
    per_page=10,
    assessment_id=None,
):

    student = get_student_profile(actor_user_id)

    if student is None:

        raise AssessmentResultAccessDeniedError(
            "Student profile was not found."
        )

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

    percentage = (
        (total_marks / total_max) * Decimal("100")
        if total_max > 0
        else Decimal("0")
    )

    return {
        "total_assessments": total,
        "total_students": data.get("total_students", 1 if total else 0),
        "total_marks_obtained": total_marks.quantize(Decimal("0.01")),
        "total_max_marks": total_max.quantize(Decimal("0.01")),
        "percentage": percentage.quantize(Decimal("0.01")),
        "average_marks": Decimal(
            str(data["average_marks"] or 0)
        ).quantize(Decimal("0.01")),
        "highest_marks": Decimal(
            str(data["highest_marks"] or 0)
        ).quantize(Decimal("0.01")),
        "lowest_marks": Decimal(
            str(data["lowest_marks"] or 0)
        ).quantize(Decimal("0.01")),
        "passed": data["passed"] or 0,
        "failed": data["failed"] or 0,
    }


def get_my_result_analytics(actor_user_id):
    student = get_student_profile(actor_user_id)

    if student is None:
        raise AssessmentResultAccessDeniedError(
            "Student profile was not found."
        )

    data = get_student_analytics(student.id)

    return format_analytics(data)


def get_course_result_analytics(
    course_id,
    actor_user_id,
    actor_role,
):
    from app.models.course import Course

    course = db.session.get(Course, course_id)

    if course is None:
        raise AssessmentNotFoundError(
            "Course not found."
        )

    validate_course_access(
        course,
        actor_user_id,
        actor_role,
    )

    data = get_course_analytics(course_id)

    return format_analytics(data)


def get_assessment_result_analytics(
    assessment_id,
    actor_user_id,
    actor_role,
):
    assessment = db.session.get(
        Assessment,
        assessment_id,
    )

    if assessment is None:
        raise AssessmentNotFoundError(
            "Assessment not found."
        )

    validate_course_access(
        assessment.course,
        actor_user_id,
        actor_role,
    )

    data = get_assessment_analytics(assessment_id)

    return format_analytics(data)