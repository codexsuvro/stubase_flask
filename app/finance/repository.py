from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.finance.models import (
    FeeInvoice,
    FeeInvoiceLine,
    FeePayment,
    FeeStructure,
    StudentFeeCharge,
)


def get_fee_structure_by_id(fee_structure_id, for_update=False):
    statement = (
        select(FeeStructure)
        .options(selectinload(FeeStructure.items))
        .where(FeeStructure.id == fee_structure_id)
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def get_next_version(
    department_id,
    academic_year_id,
    semester_id,
    course_offering_id,
    fee_code,
):
    statement = select(
        func.coalesce(func.max(FeeStructure.version), 0)
    ).where(
        FeeStructure.department_id == department_id,
        FeeStructure.academic_year_id == academic_year_id,
        FeeStructure.semester_id == semester_id,
        FeeStructure.fee_code == fee_code,
    )
    if course_offering_id is None:
        statement = statement.where(
            FeeStructure.course_offering_id.is_(None)
        )
    else:
        statement = statement.where(
            FeeStructure.course_offering_id == course_offering_id
        )
    return (db.session.scalar(statement) or 0) + 1


def has_active_fee_structure(fee_structure, exclude_id=None):
    statement = select(FeeStructure.id).where(
        FeeStructure.department_id == fee_structure.department_id,
        FeeStructure.academic_year_id == fee_structure.academic_year_id,
        FeeStructure.semester_id == fee_structure.semester_id,
        FeeStructure.fee_code == fee_structure.fee_code,
        FeeStructure.status == "ACTIVE",
    )
    if fee_structure.course_offering_id is None:
        statement = statement.where(
            FeeStructure.course_offering_id.is_(None)
        )
    else:
        statement = statement.where(
            FeeStructure.course_offering_id
            == fee_structure.course_offering_id
        )
    if exclude_id is not None:
        statement = statement.where(FeeStructure.id != exclude_id)
    return db.session.scalar(statement) is not None


def list_fee_structures(
    page=1,
    per_page=20,
    academic_year_id=None,
    semester_id=None,
    department_id=None,
    course_offering_id=None,
    status=None,
):
    statement = select(FeeStructure).options(
        selectinload(FeeStructure.items)
    )

    for column, value in (
        (FeeStructure.academic_year_id, academic_year_id),
        (FeeStructure.semester_id, semester_id),
        (FeeStructure.department_id, department_id),
        (FeeStructure.course_offering_id, course_offering_id),
        (FeeStructure.status, status),
    ):
        if value is not None:
            statement = statement.where(column == value)

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    items = db.session.scalars(
        statement.order_by(
            FeeStructure.created_at.desc(),
            FeeStructure.id.desc(),
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


def get_fee_charge_by_id(charge_id, for_update=False):
    statement = select(StudentFeeCharge).where(
        StudentFeeCharge.id == charge_id
    )
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def list_fee_charges(
    page=1,
    per_page=20,
    student_id=None,
    academic_year_id=None,
    semester_id=None,
    status=None,
):
    statement = select(StudentFeeCharge)
    for column, value in (
        (StudentFeeCharge.student_id, student_id),
        (StudentFeeCharge.academic_year_id, academic_year_id),
        (StudentFeeCharge.semester_id, semester_id),
        (StudentFeeCharge.status, status),
    ):
        if value is not None:
            statement = statement.where(column == value)

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0

    items = db.session.scalars(
        statement.order_by(
            StudentFeeCharge.created_at.desc(),
            StudentFeeCharge.id.desc(),
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


def get_invoice_by_id(invoice_id, for_update=False):
    statement = select(FeeInvoice).where(FeeInvoice.id == invoice_id)
    if for_update:
        statement = statement.with_for_update()
    return db.session.scalar(statement)


def list_invoices(
    page=1,
    per_page=20,
    student_id=None,
    academic_year_id=None,
    semester_id=None,
    status=None,
):
    statement = select(FeeInvoice)
    for column, value in (
        (FeeInvoice.student_id, student_id),
        (FeeInvoice.academic_year_id, academic_year_id),
        (FeeInvoice.semester_id, semester_id),
        (FeeInvoice.status, status),
    ):
        if value is not None:
            statement = statement.where(column == value)

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0
    items = db.session.scalars(
        statement.order_by(
            FeeInvoice.issued_at.desc(),
            FeeInvoice.id.desc(),
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


def has_active_invoice_line(charge_id):
    return db.session.scalar(
        select(FeeInvoiceLine.id).where(
            FeeInvoiceLine.charge_id == charge_id,
            FeeInvoiceLine.status == "ACTIVE",
        )
    ) is not None


def get_payment_by_id(payment_id):
    return db.session.scalar(
        select(FeePayment).where(FeePayment.id == payment_id)
    )


def list_payments(
    page=1,
    per_page=20,
    student_id=None,
    invoice_id=None,
    payment_method=None,
):
    statement = select(FeePayment).join(FeeInvoice)
    if student_id is not None:
        statement = statement.where(FeeInvoice.student_id == student_id)
    if invoice_id is not None:
        statement = statement.where(FeePayment.invoice_id == invoice_id)
    if payment_method is not None:
        statement = statement.where(
            FeePayment.payment_method == payment_method
        )

    total_records = db.session.scalar(
        select(func.count()).select_from(
            statement.order_by(None).subquery()
        )
    ) or 0
    items = db.session.scalars(
        statement.order_by(
            FeePayment.received_at.desc(),
            FeePayment.id.desc(),
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
