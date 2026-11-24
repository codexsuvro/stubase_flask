from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.finance.models import FeeAdjustment, StudentFeeCharge
from app.scholarships.models import (
    ScholarshipApplication,
    ScholarshipAward,
    ScholarshipProgram,
)


def get_program_by_id(program_id, for_update=False):
    statement = select(ScholarshipProgram).where(
        ScholarshipProgram.id == program_id
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def list_programs(
    page=1,
    per_page=20,
    academic_year_id=None,
    semester_id=None,
    department_id=None,
    status=None,
):
    statement = select(ScholarshipProgram)
    for column, value in (
        (ScholarshipProgram.academic_year_id, academic_year_id),
        (ScholarshipProgram.semester_id, semester_id),
        (ScholarshipProgram.department_id, department_id),
        (ScholarshipProgram.status, status),
    ):
        if value is not None:
            statement = statement.where(column == value)
    return _paginate(statement, page, per_page)


def get_application_by_id(application_id, for_update=False):
    statement = (
        select(ScholarshipApplication)
        .options(selectinload(ScholarshipApplication.award))
        .where(ScholarshipApplication.id == application_id)
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def list_applications(
    page=1,
    per_page=20,
    program_id=None,
    student_id=None,
    status=None,
):
    statement = select(ScholarshipApplication)
    for column, value in (
        (ScholarshipApplication.program_id, program_id),
        (ScholarshipApplication.student_id, student_id),
        (ScholarshipApplication.status, status),
    ):
        if value is not None:
            statement = statement.where(column == value)
    return _paginate(statement, page, per_page)


def get_award_by_id(award_id, for_update=False):
    statement = select(ScholarshipAward).where(
        ScholarshipAward.id == award_id
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def list_awards(
    page=1,
    per_page=20,
    student_id=None,
    program_id=None,
    status=None,
):
    statement = select(ScholarshipAward)
    for column, value in (
        (ScholarshipAward.student_id, student_id),
        (ScholarshipAward.program_id, program_id),
        (ScholarshipAward.status, status),
    ):
        if value is not None:
            statement = statement.where(column == value)
    return _paginate(statement, page, per_page)


def get_adjustment_by_id(adjustment_id, for_update=False):
    statement = select(FeeAdjustment).where(
        FeeAdjustment.id == adjustment_id
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def list_adjustments(
    page=1,
    per_page=20,
    student_id=None,
    charge_id=None,
    kind=None,
    status=None,
):
    statement = select(FeeAdjustment).join(
        StudentFeeCharge,
        StudentFeeCharge.id == FeeAdjustment.charge_id,
    )
    for column, value in (
        (StudentFeeCharge.student_id, student_id),
        (FeeAdjustment.charge_id, charge_id),
        (FeeAdjustment.kind, kind),
        (FeeAdjustment.status, status),
    ):
        if value is not None:
            statement = statement.where(column == value)
    return _paginate(statement, page, per_page)


def _paginate(statement, page, per_page):
    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0
    items = db.session.scalars(
        statement.order_by(
            statement.column_descriptions[0]["entity"].created_at.desc(),
            statement.column_descriptions[0]["entity"].id.desc(),
        )
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()
    total_pages = (
        (total_records + per_page - 1) // per_page
        if total_records
        else 0
    )
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
    }
