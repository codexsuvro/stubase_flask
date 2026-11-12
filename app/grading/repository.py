from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.grading_scheme import GradingScheme
from app.models.grade_scale import GradeScale
from app.models.course_grade import CourseGrade
from app.models.enrollment import Enrollment
from app.models.assessment import Assessment
from app.models.assessment_result import AssessmentResult
from app.models.course_offering import CourseOffering


def get_scheme_by_id(scheme_id):
    statement = (
        select(GradingScheme)
        .options(selectinload(GradingScheme.grade_scales))
        .where(GradingScheme.id == scheme_id)
    )
    return db.session.scalar(statement)


def get_scheme_by_name(name):
    statement = select(GradingScheme).where(
        GradingScheme.scheme_name == name
    )
    return db.session.scalar(statement)


def list_schemes():
    statement = (
        select(GradingScheme)
        .options(selectinload(GradingScheme.grade_scales))
        .order_by(GradingScheme.scheme_name)
    )
    return db.session.scalars(statement).all()


def create_scheme(scheme):
    db.session.add(scheme)
    db.session.flush()
    return scheme


def get_enrollment(enrollment_id):
    statement = (
        select(Enrollment)
        .options(
            selectinload(Enrollment.student),
            selectinload(Enrollment.course),
            selectinload(Enrollment.offering).selectinload(
                CourseOffering.assessments
            ),
        )
        .where(Enrollment.id == enrollment_id)
    )
    return db.session.scalar(statement)


def get_course_grade_by_enrollment(enrollment_id):
    statement = select(CourseGrade).where(
        CourseGrade.enrollment_id == enrollment_id
    )
    return db.session.scalar(statement)


def create_course_grade(grade):
    db.session.add(grade)
    db.session.flush()
    return grade


def get_published_grades_for_student(student_id):
    statement = (
        select(CourseGrade)
        .join(Enrollment)
        .where(
            Enrollment.student_id == student_id,
            CourseGrade.publication_status == "PUBLISHED",
        )
        .options(
            selectinload(CourseGrade.enrollment).selectinload(
                Enrollment.course
            ),
            selectinload(CourseGrade.enrollment).selectinload(
                Enrollment.student
            ),
        )
        .order_by(
            Enrollment.academic_year,
            Enrollment.semester,
        )
    )
    return db.session.scalars(statement).all()


def get_assessment_results(enrollment_id):
    statement = (
        select(AssessmentResult)
        .join(
            Enrollment,
            Enrollment.id == AssessmentResult.enrollment_id,
        )
        .join(
            Assessment,
            Assessment.id == AssessmentResult.assessment_id,
        )
        .where(
            AssessmentResult.enrollment_id == enrollment_id,
            Assessment.offering_id == Enrollment.offering_id,
        )
    )
    return db.session.scalars(statement).all()


def get_assessments_for_offering(offering_id):
    statement = (
        select(Assessment)
        .where(Assessment.offering_id == offering_id)
        .order_by(
            Assessment.assessment_type,
            Assessment.sequence_number,
        )
    )
    return db.session.scalars(statement).all()


def get_result_for_assessment(assessment_id, enrollment_id):
    statement = select(AssessmentResult).where(
        AssessmentResult.assessment_id == assessment_id,
        AssessmentResult.enrollment_id == enrollment_id,
    )
    return db.session.scalar(statement)


def get_course_grade_by_id(grade_id):
    statement = (
        select(CourseGrade)
        .options(
            selectinload(CourseGrade.enrollment).selectinload(
                Enrollment.student
            ),
            selectinload(CourseGrade.enrollment).selectinload(
                Enrollment.course
            ),
        )
        .where(CourseGrade.id == grade_id)
    )
    return db.session.scalar(statement)