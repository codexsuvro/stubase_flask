from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.finance.models import (
    FeeStructure,
    FeeStructureItem,
    StudentFeeCharge,
)
from app.finance.repository import (
    get_fee_charge_by_id,
    get_fee_structure_by_id,
    get_next_version,
    has_active_fee_structure,
    list_fee_charges,
    list_fee_structures,
)
from app.models.academic_year import AcademicYear
from app.models.course_offering import CourseOffering
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.semester import Semester
from app.models.student import Student


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


def void_fee_charge(charge_id, actor_user_id, reason):
    charge = get_fee_charge_by_id(charge_id, for_update=True)
    if charge is None:
        raise FeeChargeNotFoundError("Fee charge not found.")
    if charge.status == "VOID":
        return charge

    charge.status = "VOID"
    charge.voided_at = datetime.now(UTC)
    charge.voided_by = UUID(str(actor_user_id))
    charge.void_reason = reason.strip()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return get_fee_charge_by_id(charge.id)
