from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.assessment_result import AssessmentResult
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.course_offering import CourseOffering


def create_result(data):
    result = AssessmentResult(**data)

    db.session.add(result)
    db.session.flush()

    return result


def get_result_by_id(result_id):

    stmt = (
        select(AssessmentResult)
        .options(
            selectinload(
                AssessmentResult.assessment
            ).selectinload(
                Assessment.course
            ),
            selectinload(
                AssessmentResult.assessment
            ).selectinload(
                Assessment.offering
            ),
            selectinload(
                AssessmentResult.enrollment
            ).selectinload(
                Enrollment.student
            ),
            selectinload(
                AssessmentResult.grader
            ),
        )
        .where(AssessmentResult.id == result_id)
    )

    return db.session.execute(
        stmt
    ).scalar_one_or_none()


def get_result_by_assessment_and_enrollment(
    assessment_id,
    enrollment_id,
):
    stmt = select(AssessmentResult).where(
        AssessmentResult.assessment_id == assessment_id,
        AssessmentResult.enrollment_id == enrollment_id,
    )

    return db.session.execute(
        stmt
    ).scalar_one_or_none()


def update_result(result, data):

    for key, value in data.items():
        setattr(result, key, value)

    db.session.flush()

    return result


def delete_result(result):
    db.session.delete(result)
    db.session.flush()

    return True


def list_results_paginated(
    page=1,
    per_page=10,
    assessment_id=None,
    enrollment_id=None,
    course_id=None,
    faculty_id=None,
    student_id=None,
):
    stmt = (
        select(AssessmentResult)
        .join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        )
        .join(
            Enrollment,
            AssessmentResult.enrollment_id == Enrollment.id,
        )
        .options(
            selectinload(
                AssessmentResult.assessment
            ).selectinload(
                Assessment.course
            ),
            selectinload(
                AssessmentResult.assessment
            ).selectinload(
                Assessment.offering
            ),
            selectinload(
                AssessmentResult.enrollment
            ).selectinload(
                Enrollment.student
            ),
            selectinload(
                AssessmentResult.grader
            ),
        )
    )

    count_stmt = (
        select(func.count(AssessmentResult.id))
        .join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        )
        .join(
            Enrollment,
            AssessmentResult.enrollment_id == Enrollment.id,
        )
    )

    if assessment_id is not None:
        stmt = stmt.where(
            AssessmentResult.assessment_id == assessment_id
        )
        count_stmt = count_stmt.where(
            AssessmentResult.assessment_id == assessment_id
        )

    if enrollment_id is not None:
        stmt = stmt.where(
            AssessmentResult.enrollment_id == enrollment_id
        )
        count_stmt = count_stmt.where(
            AssessmentResult.enrollment_id == enrollment_id
        )

    if course_id is not None:
        stmt = stmt.where(
            Assessment.course_id == course_id
        )
        count_stmt = count_stmt.where(
            Assessment.course_id == course_id
        )

    if faculty_id is not None:
        stmt = (
            stmt
            .join(
                CourseOffering,
                Assessment.offering_id == CourseOffering.id,
            )
            .where(CourseOffering.faculty_id == faculty_id)
        )

        count_stmt = (
            count_stmt
            .join(
                CourseOffering,
                Assessment.offering_id == CourseOffering.id,
            )
            .where(CourseOffering.faculty_id == faculty_id)
        )

    if student_id is not None:
        stmt = stmt.where(
            Enrollment.student_id == student_id
        )
        count_stmt = count_stmt.where(
            Enrollment.student_id == student_id
        )

    total = db.session.scalar(count_stmt) or 0

    stmt = (
        stmt
        .order_by(
            AssessmentResult.created_at.desc(),
            AssessmentResult.id.desc(),
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    items = db.session.scalars(stmt).unique().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


def commit():
    db.session.commit()


def rollback():
    db.session.rollback()
    

def get_student_analytics(student_id):
    stmt = (
        select(
            func.count(AssessmentResult.id).label("total_assessments"),
            func.coalesce(
                func.sum(AssessmentResult.marks_obtained), 0
            ).label("total_marks_obtained"),
            func.coalesce(
                func.sum(Assessment.max_marks), 0
            ).label("total_max_marks"),
            func.coalesce(
                func.avg(AssessmentResult.marks_obtained), 0
            ).label("average_marks"),
            func.coalesce(
                func.max(AssessmentResult.marks_obtained), 0
            ).label("highest_marks"),
            func.coalesce(
                func.min(AssessmentResult.marks_obtained), 0
            ).label("lowest_marks"),
            func.sum(
                case(
                    (
                        AssessmentResult.marks_obtained
                        >= Assessment.passing_marks,
                        1,
                    ),
                    else_=0,
                )
            ).label("passed"),
            func.sum(
                case(
                    (
                        AssessmentResult.marks_obtained
                        < Assessment.passing_marks,
                        1,
                    ),
                    else_=0,
                )
            ).label("failed"),
        )
        .join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        )
        .join(
            Enrollment,
            AssessmentResult.enrollment_id == Enrollment.id,
        )
        .where(Enrollment.student_id == student_id)
    )

    return db.session.execute(stmt).mappings().one()


def get_course_analytics(course_id):
    stmt = (
        select(
            func.count(AssessmentResult.id).label("total_results"),
            func.count(
                func.distinct(Enrollment.student_id)
            ).label("total_students"),
            func.coalesce(
                func.sum(AssessmentResult.marks_obtained), 0
            ).label("total_marks_obtained"),
            func.coalesce(
                func.sum(Assessment.max_marks), 0
            ).label("total_max_marks"),
            func.coalesce(
                func.avg(AssessmentResult.marks_obtained), 0
            ).label("average_marks"),
            func.coalesce(
                func.max(AssessmentResult.marks_obtained), 0
            ).label("highest_marks"),
            func.coalesce(
                func.min(AssessmentResult.marks_obtained), 0
            ).label("lowest_marks"),
            func.sum(
                case(
                    (
                        AssessmentResult.marks_obtained
                        >= Assessment.passing_marks,
                        1,
                    ),
                    else_=0,
                )
            ).label("passed"),
            func.sum(
                case(
                    (
                        AssessmentResult.marks_obtained
                        < Assessment.passing_marks,
                        1,
                    ),
                    else_=0,
                )
            ).label("failed"),
        )
        .join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        )
        .join(
            Enrollment,
            AssessmentResult.enrollment_id == Enrollment.id,
        )
        .where(Assessment.course_id == course_id)
    )

    return db.session.execute(stmt).mappings().one()


def get_assessment_analytics(assessment_id):
    stmt = (
        select(
            func.count(AssessmentResult.id).label("total_results"),

            func.count(
                func.distinct(Enrollment.student_id)
            ).label("total_students"),

            func.coalesce(
                func.sum(AssessmentResult.marks_obtained), 0
            ).label("total_marks_obtained"),

            func.coalesce(
                func.sum(Assessment.max_marks), 0
            ).label("total_max_marks"),

            func.coalesce(
                func.avg(AssessmentResult.marks_obtained), 0
            ).label("average_marks"),

            func.coalesce(
                func.max(AssessmentResult.marks_obtained), 0
            ).label("highest_marks"),

            func.coalesce(
                func.min(AssessmentResult.marks_obtained), 0
            ).label("lowest_marks"),

            func.sum(
                case(
                    (
                        AssessmentResult.marks_obtained
                        >= Assessment.passing_marks,
                        1,
                    ),
                    else_=0,
                )
            ).label("passed"),

            func.sum(
                case(
                    (
                        AssessmentResult.marks_obtained
                        < Assessment.passing_marks,
                        1,
                    ),
                    else_=0,
                )
            ).label("failed"),
        )
        .join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        )
        .join(
            Enrollment,
            AssessmentResult.enrollment_id == Enrollment.id,
        )
        .where(AssessmentResult.assessment_id == assessment_id)
    )

    return db.session.execute(stmt).mappings().one()