
from decimal import Decimal, ROUND_HALF_UP
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.grading_scheme import GradingScheme
from app.models.grade_scale import GradeScale
from app.models.course_grade import CourseGrade
from app.models.faculty import Faculty
from app.grading import repository as repo


class GradingError(Exception):
    pass


class GradingNotFoundError(GradingError):
    pass


class GradingValidationError(GradingError):
    pass


class GradingAccessDeniedError(GradingError):
    pass


class DuplicateGradingSchemeError(GradingError):
    pass


HUNDRED = Decimal("100")
TWO_PLACES = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(
        TWO_PLACES,
        rounding=ROUND_HALF_UP,
    )


def validate_grade_scales(scales):
    if not scales:
        raise GradingValidationError(
            "At least one grade scale is required."
        )

    ordered = sorted(
        scales,
        key=lambda item: Decimal(str(item["min_percentage"])),
    )

    for index, scale in enumerate(ordered):
        minimum = Decimal(str(scale["min_percentage"]))
        maximum = Decimal(str(scale["max_percentage"]))

        if minimum > maximum:
            raise GradingValidationError(
                "Invalid grade percentage range."
            )

        if index > 0:
            previous_max = Decimal(
                str(ordered[index - 1]["max_percentage"])
            )

            if minimum <= previous_max:
                raise GradingValidationError(
                    "Grade percentage ranges must not overlap."
                )

            if minimum - previous_max != Decimal("0.01"):
                raise GradingValidationError(
                    "Grade percentage ranges must be continuous."
                )

    if (
        Decimal(str(ordered[0]["min_percentage"])) != Decimal("0")
        or Decimal(str(ordered[-1]["max_percentage"])) != HUNDRED
    ):
        raise GradingValidationError(
            "Grade ranges must cover 0 to 100."
        )


def create_grading_scheme(data):
    if repo.get_scheme_by_name(data["scheme_name"]):
        raise DuplicateGradingSchemeError(
            "A grading scheme with this name already exists."
        )

    validate_grade_scales(data["grade_scales"])

    scheme = GradingScheme(
        scheme_name=data["scheme_name"],
        description=data.get("description"),
        status="ACTIVE",
    )

    for item in data["grade_scales"]:
        scheme.grade_scales.append(
            GradeScale(
                letter_grade=item["letter_grade"].upper(),
                min_percentage=item["min_percentage"],
                max_percentage=item["max_percentage"],
                grade_point=item["grade_point"],
                is_passing=item["is_passing"],
            )
        )

    try:
        repo.create_scheme(scheme)
        db.session.commit()
        return scheme

    except IntegrityError:
        db.session.rollback()
        raise DuplicateGradingSchemeError(
            "Could not create grading scheme."
        )


def list_grading_schemes():
    return repo.list_schemes()


def update_grading_scheme(scheme_id, data):
    scheme = repo.get_scheme_by_id(scheme_id)

    if not scheme:
        raise GradingNotFoundError(
            "Grading scheme not found."
        )

    if scheme.course_grades:
        raise GradingValidationError(
            "A grading scheme already used for grades cannot be modified."
        )

    if "scheme_name" in data:
        existing = repo.get_scheme_by_name(data["scheme_name"])

        if existing and existing.id != scheme.id:
            raise DuplicateGradingSchemeError(
                "Grading scheme name already exists."
            )

        scheme.scheme_name = data["scheme_name"]

    if "description" in data:
        scheme.description = data["description"]

    if "status" in data:
        scheme.status = data["status"]

    db.session.commit()
    return scheme


def calculate_course_grade(enrollment_id, scheme_id, user=None):
    enrollment = repo.get_enrollment(enrollment_id)

    if not enrollment:
        raise GradingNotFoundError(
            "Enrollment not found."
        )

    if enrollment.status != "ENROLLED":
        raise GradingValidationError(
            "Only active enrollments can be graded."
        )

    offering = enrollment.offering

    if not offering:
        raise GradingValidationError(
            "Enrollment is not associated with a course offering."
        )

    if offering.course_id != enrollment.course_id:
        raise GradingValidationError(
            "Enrollment course does not match its course offering."
        )

    # Faculty can grade only their assigned course offerings.
    if user and user.role.role_name == "FACULTY":
        faculty = db.session.scalar(
            select(Faculty).where(Faculty.user_id == user.id)
        )

        if not faculty or offering.faculty_id != faculty.id:
            raise GradingAccessDeniedError(
                "You are not authorized to grade this course offering."
            )

    scheme = repo.get_scheme_by_id(scheme_id)

    if not scheme or scheme.status != "ACTIVE":
        raise GradingNotFoundError(
            "Active grading scheme not found."
        )

    assessments = repo.get_assessments_for_offering(offering.id)

    if not assessments:
        raise GradingValidationError(
            "No assessments found for this offering."
        )

    for assessment in assessments:
        if assessment.course_id != enrollment.course_id:
            raise GradingValidationError(
                "An assessment is linked to a different course."
            )

    total_weightage = sum(
        (
            Decimal(str(assessment.weightage))
            for assessment in assessments
        ),
        Decimal("0"),
    )

    if total_weightage != HUNDRED:
        raise GradingValidationError(
            f"Assessment weightage must total 100. "
            f"Current total: {total_weightage}."
        )

    weighted_percentage = Decimal("0")
    total_marks = Decimal("0")

    for assessment in assessments:
        result = repo.get_result_for_assessment(
            assessment.id,
            enrollment.id,
        )

        if not result:
            raise GradingValidationError(
                f"Missing result for assessment: "
                f"{assessment.assessment_name}."
            )

        maximum = Decimal(str(assessment.max_marks))
        passing = Decimal(str(assessment.passing_marks))
        obtained = Decimal(str(result.marks_obtained))

        if maximum <= 0:
            raise GradingValidationError(
                "Assessment maximum marks must be greater than zero."
            )

        if passing < 0 or passing > maximum:
            raise GradingValidationError(
                "Assessment passing marks configuration is invalid."
            )

        if obtained < 0 or obtained > maximum:
            raise GradingValidationError(
                f"Invalid marks for assessment: "
                f"{assessment.assessment_name}."
            )

        assessment_percentage = (
            obtained / maximum
        ) * HUNDRED

        weighted_percentage += (
            assessment_percentage
            * Decimal(str(assessment.weightage))
            / HUNDRED
        )

        total_marks += obtained

    percentage = money(weighted_percentage)

    matched_scale = next(
        (
            scale
            for scale in scheme.grade_scales
            if Decimal(str(scale.min_percentage))
            <= percentage
            <= Decimal(str(scale.max_percentage))
        ),
        None,
    )

    if not matched_scale:
        raise GradingValidationError(
            "No grade scale matches the calculated percentage."
        )

    existing_grade = repo.get_course_grade_by_enrollment(
        enrollment.id
    )

    if (
        existing_grade
        and existing_grade.publication_status == "PUBLISHED"
    ):
        raise GradingValidationError(
            "Published grades cannot be recalculated."
        )

    grade_data = {
        "enrollment_id": enrollment.id,
        "grading_scheme_id": scheme.id,
        "total_marks": money(total_marks),
        "percentage": percentage,
        "letter_grade": matched_scale.letter_grade,
        "grade_point": matched_scale.grade_point,
        "result_status": (
            "PASS" if matched_scale.is_passing else "FAIL"
        ),
        "publication_status": "DRAFT",
    }

    if existing_grade:
        for key, value in grade_data.items():
            setattr(existing_grade, key, value)

        grade = existing_grade

    else:
        grade = CourseGrade(**grade_data)
        repo.create_course_grade(grade)

    db.session.commit()
    return grade


def publish_course_grade(grade_id, publisher_id):
    grade = repo.get_course_grade_by_id(grade_id)

    if not grade:
        raise GradingNotFoundError(
            "Course grade not found."
        )

    if grade.publication_status == "PUBLISHED":
        raise GradingValidationError(
            "Course grade is already published."
        )

    grade.publication_status = "PUBLISHED"
    grade.published_at = datetime.now(UTC)
    grade.published_by = publisher_id

    db.session.commit()
    return grade


def get_student_transcript(student):
    grades = repo.get_published_grades_for_student(student.id)

    courses = []
    total_credits = 0
    earned_credits = 0
    weighted_points = Decimal("0")

    for grade in grades:
        enrollment = grade.enrollment
        course = enrollment.course
        credits = course.credits

        total_credits += credits

        if grade.result_status == "PASS":
            earned_credits += credits

        weighted_points += (
            Decimal(str(grade.grade_point))
            * Decimal(str(credits))
        )

        courses.append({
            "course_code": course.course_code,
            "course_name": course.course_name,
            "credits": credits,
            "academic_year": enrollment.academic_year,
            "semester": enrollment.semester,
            "percentage": grade.percentage,
            "letter_grade": grade.letter_grade,
            "grade_point": grade.grade_point,
            "result_status": grade.result_status,
        })

    cgpa = (
        money(weighted_points / Decimal(total_credits))
        if total_credits
        else Decimal("0.00")
    )

    return {
        "student_id": student.student_id,
        "student_name": (
            f"{student.first_name} {student.last_name}"
        ),
        "courses": courses,
        "total_credits": total_credits,
        "earned_credits": earned_credits,
        "cgpa": cgpa,
    }
