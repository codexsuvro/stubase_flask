from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.assignments.storage import AssignmentStorageError, delete_pdf
from app.finance.models import FeeAdjustment, StudentFeeCharge
from app.finance.repository import get_fee_charge_by_id
from app.grading.service import get_student_transcript
from app.models.academic_year import AcademicYear
from app.models.course_offering import CourseOffering
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.semester import Semester
from app.models.student import Student
from app.scholarships.models import (
    ScholarshipApplication,
    ScholarshipApplicationDocument,
    ScholarshipAward,
    ScholarshipProgram,
)
from app.scholarships.repository import (
    get_adjustment_by_id,
    get_application_by_id,
    get_award_by_id,
    get_program_by_id,
    list_adjustments,
    list_applications,
    list_awards,
    list_programs,
)
from app.scholarships.storage import (
    ScholarshipStorageError,
    create_scholarship_document_url,
    store_scholarship_document,
)


CENT = Decimal("0.01")


class ScholarshipModuleError(Exception):
    status_code = 422


class ScholarshipNotFoundError(ScholarshipModuleError):
    status_code = 404


class ScholarshipConflictError(ScholarshipModuleError):
    status_code = 409


class ScholarshipValidationError(ScholarshipModuleError):
    status_code = 422


class ScholarshipAccessDeniedError(ScholarshipModuleError):
    status_code = 403


class ScholarshipStorageUnavailableError(ScholarshipModuleError):
    status_code = 503


def _normalize_user_id(user_id):
    try:
        return user_id if isinstance(user_id, UUID) else UUID(str(user_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ScholarshipAccessDeniedError(
            "Invalid authenticated user ID."
        ) from exc


def _commit_conflict(message):
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ScholarshipConflictError(message) from exc
    except Exception:
        db.session.rollback()
        raise


def _student_for_user(user_id):
    student = db.session.scalar(
        select(Student).where(
            Student.user_id == _normalize_user_id(user_id)
        )
    )
    if student is None:
        raise ScholarshipNotFoundError("Student profile not found.")
    return student


def _aware(value, name):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ScholarshipValidationError(
            f"{name} must include a timezone offset (ISO 8601)."
        )
    return value


def _validate_program_scope(data):
    academic_year = db.session.get(
        AcademicYear,
        data["academic_year_id"],
    )
    if academic_year is None:
        raise ScholarshipNotFoundError("Academic year not found.")
    if academic_year.status == "COMPLETED":
        raise ScholarshipConflictError(
            "A scholarship cannot target a completed academic year."
        )

    semester_id = data.get("semester_id")
    semester = None
    if semester_id is not None:
        semester = db.session.get(Semester, semester_id)
        if semester is None:
            raise ScholarshipNotFoundError("Semester not found.")
        if semester.academic_year_id != academic_year.id:
            raise ScholarshipConflictError(
                "The selected semester does not belong to the academic year."
            )
        if semester.status == "COMPLETED":
            raise ScholarshipConflictError(
                "A scholarship cannot target a completed semester."
            )

    department_id = data.get("department_id")
    if department_id is not None and db.session.get(
        Department,
        department_id,
    ) is None:
        raise ScholarshipNotFoundError("Department not found.")

    open_at = _aware(data["application_open_at"], "application_open_at")
    close_at = _aware(data["application_close_at"], "application_close_at")
    if close_at <= open_at:
        raise ScholarshipValidationError(
            "application_close_at must be later than application_open_at."
        )

    award_type = data["award_type"].strip().upper()
    award_value = Decimal(str(data["award_value"]))
    max_award_amount = data.get("max_award_amount")
    if max_award_amount is not None:
        max_award_amount = Decimal(str(max_award_amount))
    total_budget_amount = data.get("total_budget_amount")
    if total_budget_amount is not None:
        total_budget_amount = Decimal(str(total_budget_amount))
    max_recipients = data.get("max_recipients")
    if award_value <= 0:
        raise ScholarshipValidationError(
            "award_value must be greater than zero."
        )
    if award_type == "PERCENTAGE" and award_value > 100:
        raise ScholarshipValidationError(
            "A percentage award cannot exceed 100 percent."
        )
    if award_type == "FIXED" and max_award_amount is not None:
        raise ScholarshipValidationError(
            "max_award_amount is only valid for percentage awards."
        )
    if (
        total_budget_amount is not None
        and award_type == "PERCENTAGE"
        and max_award_amount is None
    ):
        raise ScholarshipValidationError(
            "A percentage program with a total budget must set "
            "max_award_amount per recipient."
        )
    if max_recipients is not None and max_recipients < 1:
        raise ScholarshipValidationError("max_recipients must be positive.")
    return academic_year, semester, award_type, award_value, max_award_amount


def create_program(data):
    _, _, award_type, award_value, max_award_amount = (
        _validate_program_scope(data)
    )
    program = ScholarshipProgram(
        code=data["code"].strip().upper(),
        name=data["name"].strip(),
        description=data.get("description"),
        academic_year_id=data["academic_year_id"],
        semester_id=data.get("semester_id"),
        department_id=data.get("department_id"),
        application_open_at=data["application_open_at"],
        application_close_at=data["application_close_at"],
        min_cgpa=data.get("min_cgpa"),
        award_type=award_type,
        award_value=award_value,
        max_award_amount=max_award_amount,
        total_budget_amount=data.get("total_budget_amount"),
        max_recipients=data.get("max_recipients"),
        currency_code=data.get("currency_code", "INR").strip().upper(),
        status="DRAFT",
    )
    db.session.add(program)
    _commit_conflict("A scholarship program with this code already exists.")
    return program


def get_program(program_id):
    program = get_program_by_id(program_id)
    if program is None:
        raise ScholarshipNotFoundError("Scholarship program not found.")
    return program


def list_admin_programs(
    page=1,
    per_page=20,
    academic_year_id=None,
    semester_id=None,
    department_id=None,
    status=None,
):
    return list_programs(
        page=page,
        per_page=per_page,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        department_id=department_id,
        status=status,
    )


def update_program(program_id, data):
    program = get_program_by_id(program_id, for_update=True)
    if program is None:
        raise ScholarshipNotFoundError("Scholarship program not found.")
    if program.status != "DRAFT":
        raise ScholarshipConflictError(
            "Only DRAFT scholarship programs can be updated."
        )

    current = {
        "academic_year_id": program.academic_year_id,
        "semester_id": program.semester_id,
        "department_id": program.department_id,
        "application_open_at": program.application_open_at,
        "application_close_at": program.application_close_at,
        "award_type": program.award_type,
        "award_value": program.award_value,
        "max_award_amount": program.max_award_amount,
        "total_budget_amount": program.total_budget_amount,
        "max_recipients": program.max_recipients,
    }
    current.update(data)
    _validate_program_scope(current)

    for field in (
        "code",
        "name",
        "description",
        "academic_year_id",
        "semester_id",
        "department_id",
        "application_open_at",
        "application_close_at",
        "min_cgpa",
        "award_type",
        "award_value",
        "max_award_amount",
        "total_budget_amount",
        "max_recipients",
        "currency_code",
    ):
        if field in data:
            value = data[field]
            if field in {"code", "currency_code", "award_type"}:
                value = value.strip().upper()
            elif field == "name":
                value = value.strip()
            setattr(program, field, value)
    _commit_conflict("The scholarship program conflicts with existing data.")
    return program


def open_program(program_id):
    program = get_program_by_id(program_id, for_update=True)
    if program is None:
        raise ScholarshipNotFoundError("Scholarship program not found.")
    if program.status != "DRAFT":
        raise ScholarshipConflictError(
            "Only DRAFT scholarship programs can be opened."
        )
    if program.application_close_at <= datetime.now(UTC):
        raise ScholarshipConflictError(
            "An expired scholarship application window cannot be opened."
        )
    _validate_program_scope(
        {
            "academic_year_id": program.academic_year_id,
            "semester_id": program.semester_id,
            "department_id": program.department_id,
            "application_open_at": program.application_open_at,
            "application_close_at": program.application_close_at,
            "award_type": program.award_type,
            "award_value": program.award_value,
            "max_award_amount": program.max_award_amount,
            "total_budget_amount": program.total_budget_amount,
            "max_recipients": program.max_recipients,
        }
    )
    program.status = "OPEN"
    program.opened_at = datetime.now(UTC)
    _commit_conflict("The scholarship program could not be opened.")
    return program


def close_program(program_id):
    program = get_program_by_id(program_id, for_update=True)
    if program is None:
        raise ScholarshipNotFoundError("Scholarship program not found.")
    if program.status == "CLOSED":
        return program
    if program.status != "OPEN":
        raise ScholarshipConflictError(
            "Only OPEN scholarship programs can be closed."
        )
    program.status = "CLOSED"
    program.closed_at = datetime.now(UTC)
    _commit_conflict("The scholarship program could not be closed.")
    return program


def archive_program(program_id):
    program = get_program_by_id(program_id, for_update=True)
    if program is None:
        raise ScholarshipNotFoundError("Scholarship program not found.")
    if program.status == "ARCHIVED":
        return program
    if program.status == "OPEN":
        raise ScholarshipConflictError(
            "Close an OPEN scholarship program before archiving it."
        )
    program.status = "ARCHIVED"
    program.archived_at = datetime.now(UTC)
    _commit_conflict("The scholarship program could not be archived.")
    return program


def _has_program_enrollment(student, program):
    statement = (
        select(Enrollment.id)
        .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
        .join(Semester, CourseOffering.semester_id == Semester.id)
        .where(
            Enrollment.student_id == student.id,
            Enrollment.status == "ENROLLED",
            Semester.academic_year_id == program.academic_year_id,
        )
    )
    if program.semester_id is not None:
        statement = statement.where(
            CourseOffering.semester_id == program.semester_id
        )
    return db.session.scalar(statement) is not None


def _is_eligible(student, program):
    if (
        program.department_id is not None
        and student.department_id != program.department_id
    ):
        return False
    if not _has_program_enrollment(student, program):
        return False
    if program.min_cgpa is not None:
        transcript = get_student_transcript(student)
        if Decimal(str(transcript["cgpa"])) < program.min_cgpa:
            return False
    return True


def list_open_programs(user_id, page=1, per_page=20):
    student = _student_for_user(user_id)
    now = datetime.now(UTC)
    statement = (
        select(ScholarshipProgram)
        .where(
            ScholarshipProgram.status == "OPEN",
            ScholarshipProgram.application_open_at <= now,
            ScholarshipProgram.application_close_at > now,
        )
        .order_by(
            ScholarshipProgram.application_close_at,
            ScholarshipProgram.name,
        )
    )
    eligible = [
        program
        for program in db.session.scalars(statement).all()
        if _is_eligible(student, program)
    ]
    total_records = len(eligible)
    start = (page - 1) * per_page
    items = eligible[start:start + per_page]
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


def submit_application(program_id, user_id, statement):
    program = get_program(program_id)
    now = datetime.now(UTC)
    if (
        program.status != "OPEN"
        or now < program.application_open_at
        or now >= program.application_close_at
    ):
        raise ScholarshipConflictError(
            "This scholarship is not accepting applications."
        )
    student = _student_for_user(user_id)
    if not _is_eligible(student, program):
        raise ScholarshipConflictError(
            "You do not meet this scholarship's eligibility requirements."
        )
    application = ScholarshipApplication(
        program_id=program.id,
        student_id=student.id,
        statement=statement.strip(),
        status="SUBMITTED",
        submitted_at=now,
    )
    db.session.add(application)
    _commit_conflict(
        "You have already applied to this scholarship program."
    )
    return application


def list_my_applications(user_id, page=1, per_page=20, status=None):
    student = _student_for_user(user_id)
    return list_applications(
        page=page,
        per_page=per_page,
        student_id=student.id,
        status=status,
    )


def list_admin_applications(
    page=1,
    per_page=20,
    program_id=None,
    student_id=None,
    status=None,
):
    return list_applications(
        page=page,
        per_page=per_page,
        program_id=program_id,
        student_id=student_id,
        status=status,
    )


def get_application_for_user(application_id, user_id, role):
    application = get_application_by_id(application_id)
    if application is None:
        raise ScholarshipNotFoundError("Scholarship application not found.")
    if role != "ADMIN":
        student = _student_for_user(user_id)
        if application.student_id != student.id:
            raise ScholarshipAccessDeniedError(
                "You can view only your own scholarship applications."
            )
    return application


def _read_supporting_pdf(upload):
    filename = secure_filename(upload.filename or "")
    if not filename or not filename.lower().endswith(".pdf"):
        raise ScholarshipValidationError(
            "A PDF file with a .pdf filename is required."
        )
    max_bytes = current_app.config["ASSIGNMENT_PDF_MAX_BYTES"]
    content = upload.stream.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ScholarshipValidationError(
            f"PDF files cannot exceed {max_bytes} bytes."
        )
    if not content or b"%PDF-" not in content[:1024]:
        raise ScholarshipValidationError(
            "The uploaded file does not have a valid PDF header."
        )
    return filename, content


def add_application_document(application_id, user_id, upload):
    application = get_application_by_id(application_id, for_update=True)
    if application is None:
        raise ScholarshipNotFoundError("Scholarship application not found.")
    student = _student_for_user(user_id)
    if application.student_id != student.id:
        raise ScholarshipAccessDeniedError(
            "You can upload documents only to your own application."
        )
    if application.status != "SUBMITTED":
        raise ScholarshipConflictError(
            "Documents can be added only to a SUBMITTED application."
        )
    now = datetime.now(UTC)
    if (
        application.program.status != "OPEN"
        or now < application.program.application_open_at
        or now >= application.program.application_close_at
    ):
        raise ScholarshipConflictError(
            "The scholarship program is not accepting supporting documents."
        )
    if len(application.documents) >= 5:
        raise ScholarshipConflictError(
            "An application can have at most five supporting documents."
        )
    filename, content = _read_supporting_pdf(upload)
    document_id = uuid4()
    object_key = (
        f"scholarship-applications/{application.id}/"
        f"{document_id}.pdf"
    )
    try:
        store_scholarship_document(object_key, content)
    except ScholarshipStorageError as exc:
        raise ScholarshipStorageUnavailableError(str(exc)) from exc

    document = ScholarshipApplicationDocument(
        id=document_id,
        application_id=application.id,
        object_key=object_key,
        filename=filename,
        uploaded_at=datetime.now(UTC),
        uploaded_by=_normalize_user_id(user_id),
    )
    db.session.add(document)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            delete_pdf(object_key)
        except AssignmentStorageError:
            current_app.logger.exception(
                "Could not remove scholarship PDF object %s after a database failure.",
                object_key,
            )
        raise
    return document


def list_application_documents(application_id, user_id, role):
    application = get_application_for_user(
        application_id,
        user_id,
        role,
    )
    return {"items": application.documents}


def get_application_document_url(
    application_id,
    document_id,
    user_id,
    role,
):
    application = get_application_for_user(
        application_id,
        user_id,
        role,
    )
    document = db.session.scalar(
        select(ScholarshipApplicationDocument).where(
            ScholarshipApplicationDocument.id == document_id,
            ScholarshipApplicationDocument.application_id == application.id,
        )
    )
    if document is None:
        raise ScholarshipNotFoundError(
            "Scholarship application document not found."
        )
    try:
        return create_scholarship_document_url(
            document.object_key,
            document.filename,
        )
    except ScholarshipStorageError as exc:
        raise ScholarshipStorageUnavailableError(str(exc)) from exc


def withdraw_application(application_id, user_id):
    application = get_application_by_id(application_id, for_update=True)
    if application is None:
        raise ScholarshipNotFoundError("Scholarship application not found.")
    student = _student_for_user(user_id)
    if application.student_id != student.id:
        raise ScholarshipAccessDeniedError(
            "You can withdraw only your own scholarship applications."
        )
    if application.status != "SUBMITTED":
        raise ScholarshipConflictError(
            "Only SUBMITTED scholarship applications can be withdrawn."
        )
    application.status = "WITHDRAWN"
    _commit_conflict("The scholarship application could not be withdrawn.")
    return application


def decide_application(
    application_id,
    actor_user_id,
    approve,
    award_value=None,
    award_reason=None,
    decision_notes=None,
):
    application = get_application_by_id(application_id, for_update=True)
    if application is None:
        raise ScholarshipNotFoundError("Scholarship application not found.")
    if application.status != "SUBMITTED":
        raise ScholarshipConflictError(
            "Only SUBMITTED scholarship applications can be reviewed."
        )

    program = get_program_by_id(application.program_id, for_update=True)
    if program.status == "ARCHIVED":
        raise ScholarshipConflictError(
            "Applications for an archived program cannot be reviewed."
        )
    if approve:
        award_value = Decimal(str(award_value))
        if award_value <= 0 or award_value > program.award_value:
            raise ScholarshipValidationError(
                "The approved award value must be positive and cannot exceed "
                "the published program value."
            )
        commitment = (
            award_value
            if program.award_type == "FIXED"
            else program.max_award_amount
        )
        existing_awards = select(
            func.count(ScholarshipAward.id),
            func.coalesce(
                func.sum(
                    ScholarshipAward.award_value
                    if program.award_type == "FIXED"
                    else ScholarshipAward.max_award_amount
                ),
                0,
            ),
        ).where(
            ScholarshipAward.program_id == program.id,
            ScholarshipAward.status == "ACTIVE",
        )
        active_count, committed_budget = db.session.execute(
            existing_awards
        ).one()
        if (
            program.max_recipients is not None
            and active_count >= program.max_recipients
        ):
            raise ScholarshipConflictError(
                "The scholarship program has reached its recipient limit."
            )
        if (
            program.total_budget_amount is not None
            and Decimal(str(committed_budget)) + commitment
            > program.total_budget_amount
        ):
            raise ScholarshipConflictError(
                "The scholarship program does not have enough budget "
                "for this award."
            )
        award = ScholarshipAward(
            application_id=application.id,
            program_id=program.id,
            student_id=application.student_id,
            academic_year_id=program.academic_year_id,
            semester_id=program.semester_id,
            department_id=program.department_id,
            award_type=program.award_type,
            award_value=award_value,
            max_award_amount=program.max_award_amount,
            currency_code=program.currency_code,
            status="ACTIVE",
            awarded_at=datetime.now(UTC),
            awarded_by=_normalize_user_id(actor_user_id),
            award_reason=award_reason.strip() if award_reason else None,
        )
        db.session.add(award)
        application.status = "APPROVED"
    else:
        application.status = "REJECTED"

    application.decided_at = datetime.now(UTC)
    application.decided_by = _normalize_user_id(actor_user_id)
    application.decision_notes = (
        decision_notes.strip() if decision_notes else None
    )
    _commit_conflict("The scholarship application was already reviewed.")
    return application


def list_admin_awards(
    page=1,
    per_page=20,
    student_id=None,
    program_id=None,
    status=None,
):
    return list_awards(
        page=page,
        per_page=per_page,
        student_id=student_id,
        program_id=program_id,
        status=status,
    )


def list_my_awards(user_id, page=1, per_page=20, status=None):
    student = _student_for_user(user_id)
    return list_awards(
        page=page,
        per_page=per_page,
        student_id=student.id,
        status=status,
    )


def apply_award(award_id):
    award = get_award_by_id(award_id, for_update=True)
    if award is None:
        raise ScholarshipNotFoundError("Scholarship award not found.")
    if award.status != "ACTIVE":
        raise ScholarshipConflictError(
            "Only ACTIVE scholarship awards can be applied."
        )

    statement = (
        select(StudentFeeCharge)
        .options(selectinload(StudentFeeCharge.adjustments))
        .where(
            StudentFeeCharge.student_id == award.student_id,
            StudentFeeCharge.academic_year_id == award.academic_year_id,
            StudentFeeCharge.status == "OPEN",
            StudentFeeCharge.currency_code == award.currency_code,
        )
    )
    if award.semester_id is not None:
        statement = statement.where(
            StudentFeeCharge.semester_id == award.semester_id
        )
    if award.department_id is not None:
        statement = statement.where(
            StudentFeeCharge.department_id == award.department_id
        )
    statement = statement.order_by(
        StudentFeeCharge.due_date.asc().nulls_last(),
        StudentFeeCharge.created_at,
        StudentFeeCharge.id,
    ).with_for_update()
    charges = db.session.scalars(statement).all()

    active_award_adjustments = db.session.scalars(
        select(FeeAdjustment).where(
            FeeAdjustment.scholarship_award_id == award.id,
            FeeAdjustment.status == "ACTIVE",
        )
    ).all()
    adjusted_charge_ids = {
        adjustment.charge_id for adjustment in active_award_adjustments
    }
    used_amount = sum(
        (adjustment.amount for adjustment in active_award_adjustments),
        Decimal("0.00"),
    )
    remaining_fixed = (
        award.award_value - used_amount
        if award.award_type == "FIXED"
        else None
    )
    remaining_cap = (
        award.max_award_amount - used_amount
        if award.max_award_amount is not None
        else None
    )
    new_adjustments = []
    skipped_charges = 0

    for charge in charges:
        if charge.id in adjusted_charge_ids:
            skipped_charges += 1
            continue
        balance = charge.balance_due
        if balance <= 0:
            skipped_charges += 1
            continue
        if award.award_type == "FIXED":
            if remaining_fixed is None or remaining_fixed <= 0:
                break
            amount = min(balance, remaining_fixed)
        else:
            amount = (
                charge.amount * award.award_value / Decimal("100")
            ).quantize(CENT, rounding=ROUND_HALF_UP)
            amount = min(amount, balance)
            if remaining_cap is not None:
                if remaining_cap <= 0:
                    break
                amount = min(amount, remaining_cap)
        if amount <= 0:
            skipped_charges += 1
            continue
        adjustment = FeeAdjustment(
            charge_id=charge.id,
            scholarship_award_id=award.id,
            kind="SCHOLARSHIP",
            amount=amount,
            reason=award.award_reason or award.program.name,
            status="ACTIVE",
            created_by=award.awarded_by,
        )
        new_adjustments.append(adjustment)
        if remaining_fixed is not None:
            remaining_fixed -= amount
        if remaining_cap is not None:
            remaining_cap -= amount

    try:
        db.session.add_all(new_adjustments)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ScholarshipConflictError(
            "The award was applied concurrently. Refresh and retry."
        ) from exc
    except Exception:
        db.session.rollback()
        raise

    return {
        "award_id": award.id,
        "created_adjustments": new_adjustments,
        "skipped_charges": skipped_charges,
        "total_applied": sum(
            (adjustment.amount for adjustment in new_adjustments),
            Decimal("0.00"),
        ),
        "remaining_fixed_award": remaining_fixed,
    }


def revoke_award(award_id, actor_user_id, reason):
    award = get_award_by_id(award_id, for_update=True)
    if award is None:
        raise ScholarshipNotFoundError("Scholarship award not found.")
    if award.status == "REVOKED":
        return award
    adjustments = db.session.scalars(
        select(FeeAdjustment)
        .where(
            FeeAdjustment.scholarship_award_id == award.id,
            FeeAdjustment.status == "ACTIVE",
        )
        .with_for_update()
    ).all()
    now = datetime.now(UTC)
    actor_id = _normalize_user_id(actor_user_id)
    for adjustment in adjustments:
        adjustment.status = "VOID"
        adjustment.voided_at = now
        adjustment.voided_by = actor_id
        adjustment.void_reason = reason.strip()
    award.status = "REVOKED"
    award.revoked_at = now
    award.revoked_by = actor_id
    award.revoked_reason = reason.strip()
    _commit_conflict("The scholarship award could not be revoked.")
    return award


def create_concession(data, actor_user_id):
    charge = db.session.scalar(
        select(StudentFeeCharge)
        .options(selectinload(StudentFeeCharge.adjustments))
        .where(StudentFeeCharge.id == data["charge_id"])
        .with_for_update()
    )
    if charge is None:
        raise ScholarshipNotFoundError("Fee charge not found.")
    if charge.status != "OPEN":
        raise ScholarshipConflictError(
            "Concessions can be applied only to OPEN fee charges."
        )
    amount = Decimal(str(data["amount"]))
    if amount > charge.balance_due:
        raise ScholarshipConflictError(
            "The concession cannot exceed the remaining charge balance."
        )
    adjustment = FeeAdjustment(
        charge_id=charge.id,
        kind="CONCESSION",
        amount=amount,
        reason=data["reason"].strip(),
        status="ACTIVE",
        created_by=_normalize_user_id(actor_user_id),
    )
    db.session.add(adjustment)
    _commit_conflict("The concession could not be recorded.")
    return adjustment


def void_adjustment(adjustment_id, actor_user_id, reason):
    adjustment = get_adjustment_by_id(adjustment_id)
    if adjustment is None:
        raise ScholarshipNotFoundError("Fee adjustment not found.")
    if adjustment.status == "VOID":
        return adjustment
    charge = get_fee_charge_by_id(
        adjustment.charge_id,
        for_update=True,
    )
    if charge is None:
        raise ScholarshipNotFoundError("Fee charge not found.")
    adjustment = get_adjustment_by_id(
        adjustment_id,
        for_update=True,
    )
    if adjustment is None:
        raise ScholarshipNotFoundError("Fee adjustment not found.")
    if adjustment.status == "VOID":
        return adjustment
    adjustment.status = "VOID"
    adjustment.voided_at = datetime.now(UTC)
    adjustment.voided_by = _normalize_user_id(actor_user_id)
    adjustment.void_reason = reason.strip()
    _commit_conflict("The fee adjustment could not be voided.")
    return adjustment


def list_admin_adjustments(
    page=1,
    per_page=20,
    student_id=None,
    charge_id=None,
    kind=None,
    status=None,
):
    return list_adjustments(
        page=page,
        per_page=per_page,
        student_id=student_id,
        charge_id=charge_id,
        kind=kind,
        status=status,
    )
