from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from flask import current_app

from app.extensions import db
from app.finance.models import (
    FeeAdjustment,
    FeeInvoice,
    FeeInvoiceLine,
    FeeStructure,
    FeeStructureItem,
    StudentFeeCharge,
)
from app.finance.repository import (
    get_fee_charge_by_id,
    get_invoice_by_id,
    get_fee_structure_by_id,
    has_active_invoice_line,
    get_next_version,
    has_active_fee_structure,
    list_invoices,
    list_fee_charges,
    list_fee_structures,
)
from app.finance.pdf import generate_invoice_pdf
from app.finance.storage import (
    InvoiceStorageError,
    create_invoice_pdf_url,
    delete_invoice_pdf,
    store_invoice_pdf,
)
from app.models.academic_year import AcademicYear
from app.models.course_offering import CourseOffering
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.semester import Semester
from app.models.student import Student


MAX_INVOICE_TOTAL = Decimal("999999999999.99")


class FinanceModuleError(Exception):
    status_code = 422


class FeeStructureNotFoundError(FinanceModuleError):
    status_code = 404


class FeeStructureConflictError(FinanceModuleError):
    status_code = 409


class InvalidFeeStructureStateError(FinanceModuleError):
    status_code = 409


class FeeChargeConflictError(FinanceModuleError):
    status_code = 409


class FeeChargeNotFoundError(FinanceModuleError):
    status_code = 404


class FeeInvoiceNotFoundError(FinanceModuleError):
    status_code = 404


class FeeInvoiceConflictError(FinanceModuleError):
    status_code = 409


class FeeInvoiceAccessDeniedError(FinanceModuleError):
    status_code = 403


class FeeInvoiceStorageUnavailableError(FinanceModuleError):
    status_code = 503


class FeeInvoiceValidationError(FinanceModuleError):
    status_code = 422


def _commit_fee_structure(conflict_message):
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise FeeStructureConflictError(conflict_message) from exc
    except Exception:
        db.session.rollback()
        raise


def _create_items(fee_structure, items_data):
    fee_structure.items = [
        FeeStructureItem(
            item_code=item["item_code"].strip().upper(),
            name=item["name"].strip(),
            description=item.get("description"),
            amount=item["amount"],
            is_mandatory=item.get("is_mandatory", True),
            sequence_order=item["sequence_order"],
        )
        for item in items_data
    ]


def _validate_scope(
    department_id,
    academic_year_id,
    semester_id,
    course_offering_id,
):
    department = db.session.get(Department, department_id)
    if department is None:
        raise FeeStructureNotFoundError("Department not found.")

    academic_year = db.session.get(AcademicYear, academic_year_id)
    if academic_year is None:
        raise FeeStructureNotFoundError("Academic year not found.")

    semester = db.session.get(Semester, semester_id)
    if semester is None:
        raise FeeStructureNotFoundError("Semester not found.")
    if semester.academic_year_id != academic_year.id:
        raise FeeStructureConflictError(
            "The selected semester does not belong to the academic year."
        )
    if academic_year.status == "COMPLETED" or semester.status == "COMPLETED":
        raise InvalidFeeStructureStateError(
            "Fee structures cannot target a completed academic year or semester."
        )

    course_offering = None
    if course_offering_id is not None:
        course_offering = db.session.get(CourseOffering, course_offering_id)
        if course_offering is None:
            raise FeeStructureNotFoundError("Course offering not found.")
        if course_offering.semester_id != semester.id:
            raise FeeStructureConflictError(
                "The course offering must belong to the selected semester."
            )
        if course_offering.course.department_id != department.id:
            raise FeeStructureConflictError(
                "The course offering must belong to the selected department."
            )
        if course_offering.status == "CANCELLED":
            raise InvalidFeeStructureStateError(
                "A cancelled course offering cannot have a fee structure."
            )

    return department, academic_year, semester, course_offering


def _make_item(item_data):
    return FeeStructureItem(
        item_code=item_data["item_code"].strip().upper(),
        name=item_data["name"].strip(),
        description=item_data.get("description"),
        amount=item_data["amount"],
        is_mandatory=item_data.get("is_mandatory", True),
        sequence_order=item_data["sequence_order"],
    )


def create_fee_structure(data):
    department, academic_year, semester, offering = _validate_scope(
        data["department_id"],
        data["academic_year_id"],
        data["semester_id"],
        data.get("course_offering_id"),
    )
    fee_code = data["fee_code"].strip().upper()
    version = get_next_version(
        department.id,
        academic_year.id,
        semester.id,
        offering.id if offering else None,
        fee_code,
    )
    fee_structure = FeeStructure(
        department_id=department.id,
        academic_year_id=academic_year.id,
        semester_id=semester.id,
        course_offering_id=offering.id if offering else None,
        fee_code=fee_code,
        name=data["name"].strip(),
        description=data.get("description"),
        version=version,
        currency_code=data.get("currency_code", "INR").strip().upper(),
        status="DRAFT",
    )
    _create_items(fee_structure, data["items"])
    db.session.add(fee_structure)
    _commit_fee_structure(
        "A fee structure with the same scope, code, and version already exists.",
    )
    return get_fee_structure_by_id(fee_structure.id)


def get_fee_structure(fee_structure_id):
    fee_structure = get_fee_structure_by_id(fee_structure_id)
    if fee_structure is None:
        raise FeeStructureNotFoundError("Fee structure not found.")
    return fee_structure


def get_fee_structures(
    page=1,
    per_page=20,
    academic_year_id=None,
    semester_id=None,
    department_id=None,
    course_offering_id=None,
    status=None,
):
    return list_fee_structures(
        page=page,
        per_page=per_page,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        department_id=department_id,
        course_offering_id=course_offering_id,
        status=status,
    )


def update_fee_structure(fee_structure_id, data):
    fee_structure = get_fee_structure_by_id(
        fee_structure_id,
        for_update=True,
    )
    if fee_structure is None:
        raise FeeStructureNotFoundError("Fee structure not found.")
    if fee_structure.status != "DRAFT":
        raise InvalidFeeStructureStateError(
            "Only DRAFT fee structures can be updated. Create a new version."
        )

    for field in ("name", "currency_code"):
        if field in data:
            value = data[field]
            setattr(
                fee_structure,
                field,
                value.strip().upper() if field == "currency_code" else value.strip(),
            )
    if "description" in data:
        fee_structure.description = data["description"]
    if "items" in data:
        fee_structure.items.clear()
        db.session.flush()
        fee_structure.items = [
            _make_item(item_data)
            for item_data in data["items"]
        ]

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise FeeStructureConflictError(
            "Fee structure items conflict with existing item codes or order."
        ) from exc
    except Exception:
        db.session.rollback()
        raise
    return get_fee_structure_by_id(fee_structure.id)


def activate_fee_structure(fee_structure_id):
    fee_structure = get_fee_structure_by_id(
        fee_structure_id,
        for_update=True,
    )
    if fee_structure is None:
        raise FeeStructureNotFoundError("Fee structure not found.")
    if fee_structure.status != "DRAFT":
        raise InvalidFeeStructureStateError(
            "Only DRAFT fee structures can be activated."
        )
    _validate_scope(
        fee_structure.department_id,
        fee_structure.academic_year_id,
        fee_structure.semester_id,
        fee_structure.course_offering_id,
    )
    if not fee_structure.items:
        raise InvalidFeeStructureStateError(
            "A fee structure must contain at least one item before activation."
        )
    if has_active_fee_structure(
        fee_structure,
        exclude_id=fee_structure.id,
    ):
        raise FeeStructureConflictError(
            "An active fee structure already exists for this scope and code. "
            "Archive it before activating a new version."
        )

    now = datetime.now(UTC)
    fee_structure.status = "ACTIVE"
    fee_structure.activated_at = now
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise FeeStructureConflictError(
            "An active fee structure already exists for this scope and code."
        ) from exc
    except Exception:
        db.session.rollback()
        raise
    return get_fee_structure_by_id(fee_structure.id)


def archive_fee_structure(fee_structure_id):
    fee_structure = get_fee_structure_by_id(
        fee_structure_id,
        for_update=True,
    )
    if fee_structure is None:
        raise FeeStructureNotFoundError("Fee structure not found.")
    if fee_structure.status == "ARCHIVED":
        return fee_structure

    fee_structure.status = "ARCHIVED"
    fee_structure.archived_at = datetime.now(UTC)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return get_fee_structure_by_id(fee_structure.id)


def apply_fee_structure(fee_structure_id, due_date=None):
    fee_structure = get_fee_structure_by_id(
        fee_structure_id,
        for_update=True,
    )
    if fee_structure is None:
        raise FeeStructureNotFoundError("Fee structure not found.")
    if fee_structure.status != "ACTIVE":
        raise InvalidFeeStructureStateError(
            "Only ACTIVE fee structures can be applied to students."
        )

    enrollment_statement = (
        select(Student)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(
            Student.department_id == fee_structure.department_id,
            Enrollment.status == "ENROLLED",
            Enrollment.offering_id.is_not(None),
        )
        .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
        .where(CourseOffering.semester_id == fee_structure.semester_id)
    )
    if fee_structure.course_offering_id is not None:
        enrollment_statement = enrollment_statement.where(
            Enrollment.offering_id == fee_structure.course_offering_id
        )

    students = db.session.scalars(
        enrollment_statement.distinct()
    ).all()
    student_ids = [student.id for student in students]
    if not student_ids:
        return {
            "fee_structure_id": fee_structure.id,
            "eligible_students": 0,
            "created_charges": 0,
            "existing_charges": 0,
        }

    existing_statement = select(
        StudentFeeCharge.student_id,
        StudentFeeCharge.item_code,
    ).where(
        StudentFeeCharge.student_id.in_(student_ids),
        StudentFeeCharge.department_id == fee_structure.department_id,
        StudentFeeCharge.academic_year_id
        == fee_structure.academic_year_id,
        StudentFeeCharge.semester_id == fee_structure.semester_id,
        StudentFeeCharge.fee_code == fee_structure.fee_code,
    )
    if fee_structure.course_offering_id is None:
        existing_statement = existing_statement.where(
            StudentFeeCharge.course_offering_id.is_(None)
        )
    else:
        existing_statement = existing_statement.where(
            StudentFeeCharge.course_offering_id
            == fee_structure.course_offering_id
        )
    existing = set(db.session.execute(existing_statement).all())

    charges = []
    for student in students:
        for item in fee_structure.items:
            if (student.id, item.item_code) in existing:
                continue
            charges.append(
                StudentFeeCharge(
                    student_id=student.id,
                    fee_structure_id=fee_structure.id,
                    fee_structure_item_id=item.id,
                    department_id=fee_structure.department_id,
                    academic_year_id=fee_structure.academic_year_id,
                    semester_id=fee_structure.semester_id,
                    course_offering_id=fee_structure.course_offering_id,
                    fee_code=fee_structure.fee_code,
                    item_code=item.item_code,
                    item_name=item.name,
                    item_description=item.description,
                    amount=item.amount,
                    currency_code=fee_structure.currency_code,
                    due_date=due_date,
                    status="OPEN",
                )
            )

    try:
        db.session.add_all(charges)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise FeeChargeConflictError(
            "Charges were created concurrently. Refresh the fee structure "
            "and retry to get the current charge counts."
        ) from exc
    except Exception:
        db.session.rollback()
        raise

    total_possible = len(students) * len(fee_structure.items)
    return {
        "fee_structure_id": fee_structure.id,
        "eligible_students": len(students),
        "created_charges": len(charges),
        "existing_charges": total_possible - len(charges),
    }


def get_fee_charges(
    page=1,
    per_page=20,
    student_id=None,
    academic_year_id=None,
    semester_id=None,
    status=None,
):
    return list_fee_charges(
        page=page,
        per_page=per_page,
        student_id=student_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        status=status,
    )


def get_my_fee_charges(
    user_id,
    page=1,
    per_page=20,
    academic_year_id=None,
    semester_id=None,
    status=None,
):
    student = db.session.scalar(
        select(Student).where(Student.user_id == user_id)
    )
    if student is None:
        raise FeeChargeNotFoundError("Student profile not found.")
    return get_fee_charges(
        page=page,
        per_page=per_page,
        student_id=student.id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        status=status,
    )


def create_invoice(data, actor_user_id):
    student = db.session.get(Student, data["student_id"])
    if student is None:
        raise FeeInvoiceNotFoundError("Student not found.")

    charge_ids = data["charge_ids"]
    charges = db.session.scalars(
        select(StudentFeeCharge)
        .options(selectinload(StudentFeeCharge.adjustments))
        .where(StudentFeeCharge.id.in_(charge_ids))
        .order_by(StudentFeeCharge.id)
        .with_for_update()
    ).all()
    if len(charges) != len(charge_ids):
        raise FeeInvoiceNotFoundError(
            "One or more selected fee charges were not found."
        )
    if any(charge.student_id != student.id for charge in charges):
        raise FeeInvoiceValidationError(
            "All selected charges must belong to the specified student."
        )
    if any(charge.status != "OPEN" for charge in charges):
        raise FeeInvoiceConflictError(
            "Invoices can be issued only for OPEN fee charges."
        )
    invoiced_charge_ids = set(
        db.session.scalars(
            select(FeeInvoiceLine.charge_id).where(
                FeeInvoiceLine.status == "ACTIVE",
                FeeInvoiceLine.charge_id.in_(
                    [charge.id for charge in charges]
                ),
            )
        ).all()
    )
    if invoiced_charge_ids:
        raise FeeInvoiceConflictError(
            "One or more charges are already included in an active invoice."
        )

    first_charge = charges[0]
    for charge in charges:
        if (
            charge.academic_year_id != first_charge.academic_year_id
            or charge.semester_id != first_charge.semester_id
            or charge.currency_code != first_charge.currency_code
        ):
            raise FeeInvoiceValidationError(
                "An invoice can include charges from only one semester "
                "and currency."
            )
        if charge.balance_due <= 0:
            raise FeeInvoiceConflictError(
                "Fully adjusted charges cannot be included in an invoice."
            )

    issued_at = datetime.now(UTC)
    total_amount = sum(
        (charge.balance_due for charge in charges),
        Decimal("0.00"),
    )
    if total_amount > MAX_INVOICE_TOTAL:
        raise FeeInvoiceValidationError(
            "The invoice total exceeds the supported maximum amount."
        )
    due_date = data.get("due_date")
    if due_date is None:
        existing_due_dates = [
            charge.due_date
            for charge in charges
            if charge.due_date is not None
        ]
        due_date = min(existing_due_dates) if existing_due_dates else None

    invoice_id = uuid4()
    pdf_object_key = f"finance/invoices/{invoice_id}.pdf"
    invoice = FeeInvoice(
        id=invoice_id,
        invoice_number=(
            f"INV-{issued_at:%Y%m%d}-{invoice_id.hex[:12].upper()}"
        ),
        student=student,
        academic_year_id=first_charge.academic_year_id,
        semester_id=first_charge.semester_id,
        currency_code=first_charge.currency_code,
        total_amount=total_amount,
        issued_at=issued_at,
        issued_by=UUID(str(actor_user_id)),
        due_date=due_date,
        pdf_object_key=pdf_object_key,
        status="ISSUED",
    )
    invoice.lines = [
        FeeInvoiceLine(
            charge=charge,
            fee_code=charge.fee_code,
            item_code=charge.item_code,
            item_name=charge.item_name,
            item_description=charge.item_description,
            gross_amount=charge.amount,
            adjustment_amount=charge.amount - charge.balance_due,
            amount_due=charge.balance_due,
            status="ACTIVE",
        )
        for charge in charges
    ]

    db.session.add(invoice)
    object_stored = False
    try:
        db.session.flush()
        pdf_buffer = generate_invoice_pdf(invoice)
        store_invoice_pdf(invoice.pdf_object_key, pdf_buffer.getvalue())
        object_stored = True
        db.session.commit()
    except InvoiceStorageError as exc:
        db.session.rollback()
        raise FeeInvoiceStorageUnavailableError(str(exc)) from exc
    except IntegrityError as exc:
        db.session.rollback()
        if object_stored:
            _delete_invoice_object_after_failure(pdf_object_key)
        raise FeeInvoiceConflictError(
            "One or more charges were invoiced concurrently. Refresh and retry."
        ) from exc
    except Exception:
        db.session.rollback()
        if object_stored:
            _delete_invoice_object_after_failure(pdf_object_key)
        raise
    return get_invoice_by_id(invoice.id)


def _delete_invoice_object_after_failure(object_key):
    try:
        delete_invoice_pdf(object_key)
    except InvoiceStorageError:
        current_app.logger.exception(
            "Could not remove invoice PDF object %s after a database failure.",
            object_key,
        )


def get_invoices(
    page=1,
    per_page=20,
    student_id=None,
    academic_year_id=None,
    semester_id=None,
    status=None,
):
    return list_invoices(
        page=page,
        per_page=per_page,
        student_id=student_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        status=status,
    )


def get_my_invoices(
    user_id,
    page=1,
    per_page=20,
    academic_year_id=None,
    semester_id=None,
    status=None,
):
    student = db.session.scalar(
        select(Student).where(Student.user_id == UUID(str(user_id)))
    )
    if student is None:
        raise FeeInvoiceNotFoundError("Student profile not found.")
    return get_invoices(
        page=page,
        per_page=per_page,
        student_id=student.id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        status=status,
    )


def get_invoice(invoice_id):
    invoice = get_invoice_by_id(invoice_id)
    if invoice is None:
        raise FeeInvoiceNotFoundError("Invoice not found.")
    return invoice


def get_invoice_for_user(invoice_id, user_id, role):
    invoice = get_invoice(invoice_id)
    if role != "ADMIN":
        student = db.session.scalar(
            select(Student).where(Student.user_id == UUID(str(user_id)))
        )
        if student is None:
            raise FeeInvoiceNotFoundError("Student profile not found.")
        if invoice.student_id != student.id:
            raise FeeInvoiceAccessDeniedError(
                "You can access only your own invoices."
            )
    return invoice


def get_invoice_pdf_url(invoice_id, user_id, role):
    invoice = get_invoice_for_user(invoice_id, user_id, role)
    filename = f"{invoice.invoice_number}.pdf"
    try:
        return create_invoice_pdf_url(
            invoice.pdf_object_key,
            filename,
        )
    except InvoiceStorageError as exc:
        raise FeeInvoiceStorageUnavailableError(str(exc)) from exc


def void_invoice(invoice_id, actor_user_id, reason):
    invoice = get_invoice_by_id(invoice_id, for_update=True)
    if invoice is None:
        raise FeeInvoiceNotFoundError("Invoice not found.")
    if invoice.status == "VOID":
        return invoice
    invoice.status = "VOID"
    invoice.voided_at = datetime.now(UTC)
    invoice.voided_by = UUID(str(actor_user_id))
    invoice.void_reason = reason.strip()
    for line in invoice.lines:
        line.status = "VOID"
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return get_invoice_by_id(invoice.id)


def void_fee_charge(charge_id, actor_user_id, reason):
    charge = get_fee_charge_by_id(charge_id, for_update=True)
    if charge is None:
        raise FeeChargeNotFoundError("Fee charge not found.")
    if charge.status == "VOID":
        return charge
    if has_active_invoice_line(charge.id):
        raise FeeChargeConflictError(
            "Void the active invoice before voiding this fee charge."
        )

    charge.status = "VOID"
    now = datetime.now(UTC)
    actor_id = UUID(str(actor_user_id))
    audit_reason = reason.strip()
    charge.voided_at = now
    charge.voided_by = actor_id
    charge.void_reason = audit_reason
    adjustments = db.session.scalars(
        select(FeeAdjustment).where(
            FeeAdjustment.charge_id == charge.id,
            FeeAdjustment.status == "ACTIVE",
        )
    ).all()
    for adjustment in adjustments:
        adjustment.status = "VOID"
        adjustment.voided_at = now
        adjustment.voided_by = actor_id
        adjustment.void_reason = audit_reason
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return get_fee_charge_by_id(charge.id)
