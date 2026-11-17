from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.course_offering import CourseOffering
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.student import Student
from app.assignments.models import (
    Assignment,
    AssignmentSubmission,
)
from app.assignments.repository import (
    get_assignment_by_id,
    get_submission_by_id,
    get_submission_by_assignment_student,
    list_assignments_paginated,
    list_student_assignments_paginated,
    list_submissions_paginated,
    save_assignment,
    save_submission,
    commit_changes,
)
from app.assignments.storage import (
    AssignmentStorageError,
    create_pdf_download_url,
    delete_pdf,
    store_pdf,
)


class AssignmentNotFoundError(Exception):
    pass


class SubmissionNotFoundError(Exception):
    pass


class AssignmentOfferingNotFoundError(Exception):
    pass


class AssignmentAccessDeniedError(Exception):
    pass


class AssignmentValidationError(Exception):
    pass


class AssignmentConflictError(Exception):
    pass


class AssignmentFileNotFoundError(Exception):
    pass


def _now():
    return datetime.now(UTC)


def _normalize_user_id(user_id):
    try:
        if isinstance(user_id, UUID):
            return user_id

        return UUID(str(user_id))

    except (ValueError, TypeError, AttributeError) as exc:
        raise AssignmentAccessDeniedError(
            "Invalid authenticated user ID."
        ) from exc


def _require_aware(value, field_name):
    if value.tzinfo is None or value.utcoffset() is None:
        raise AssignmentValidationError(
            f"{field_name} must include a timezone offset (ISO 8601)."
        )

    return value


def _faculty_for_user(user_id):
    user_id = _normalize_user_id(user_id)

    return db.session.scalar(
        select(Faculty).where(
            Faculty.user_id == user_id
        )
    )


def _student_for_user(user_id):
    user_id = _normalize_user_id(user_id)

    return db.session.scalar(
        select(Student).where(
            Student.user_id == user_id
        )
    )


def _validate_offering_manager(
    offering,
    actor_user_id,
    actor_role,
):
    if actor_role == "ADMIN":
        return

    if actor_role != "FACULTY":
        raise AssignmentAccessDeniedError(
            "You are not authorized to manage assignments."
        )

    faculty = _faculty_for_user(actor_user_id)

    if faculty is None or faculty.id != offering.faculty_id:
        raise AssignmentAccessDeniedError(
            "You can manage assignments only for your assigned course offerings."
        )


def _get_assignment_or_404(assignment_id):
    assignment = get_assignment_by_id(assignment_id)

    if assignment is None:
        raise AssignmentNotFoundError(
            "Assignment not found."
        )

    return assignment


def _validate_assignment_dates(
    available_from,
    due_at,
):
    available_from = _require_aware(
        available_from,
        "available_from",
    )

    due_at = _require_aware(
        due_at,
        "due_at",
    )

    if due_at <= available_from:
        raise AssignmentValidationError(
            "due_at must be later than available_from."
        )

    return available_from, due_at


def _validate_max_marks(value):
    try:
        marks = Decimal(str(value))
    except Exception as exc:
        raise AssignmentValidationError(
            "Maximum marks must be a valid decimal number."
        ) from exc

    if not marks.is_finite() or marks <= 0:
        raise AssignmentValidationError(
            "Maximum marks must be a finite number greater than zero."
        )

    if marks > Decimal("999999.99"):
        raise AssignmentValidationError(
            "Maximum marks cannot exceed 999999.99."
        )

    if marks.as_tuple().exponent < -2:
        raise AssignmentValidationError(
            "Maximum marks can have at most two decimal places."
        )

    return marks


def create_assignment(
    data,
    actor_user_id,
    actor_role,
):
    actor_user_id = _normalize_user_id(actor_user_id)

    offering = db.session.get(
        CourseOffering,
        data["offering_id"],
    )

    if offering is None:
        raise AssignmentOfferingNotFoundError(
            "Course offering not found."
        )

    _validate_offering_manager(
        offering,
        actor_user_id,
        actor_role,
    )

    if offering.status in {"CANCELLED", "CLOSED"}:
        raise AssignmentValidationError(
            "Assignments cannot be created for CLOSED or CANCELLED offerings."
        )

    available_from, due_at = _validate_assignment_dates(
        data["available_from"],
        data["due_at"],
    )

    maximum_marks = _validate_max_marks(
        data["max_marks"]
    )

    assignment_status = data.get("status", "DRAFT")

    if (
        assignment_status == "PUBLISHED"
        and offering.status != "OPEN"
    ):
        raise AssignmentValidationError(
            "An assignment can be published only for an OPEN course offering."
        )

    title = data["title"].strip()

    if len(title) < 3:
        raise AssignmentValidationError(
            "Assignment title must contain at least 3 non-whitespace characters."
        )

    assignment = Assignment(
        offering_id=offering.id,
        created_by=actor_user_id,
        title=title,
        description=data.get("description"),
        instructions=data.get("instructions"),
        max_marks=maximum_marks,
        available_from=available_from,
        due_at=due_at,
        allow_late_submissions=data.get(
            "allow_late_submissions",
            False,
        ),
        allow_resubmissions=data.get(
            "allow_resubmissions",
            False,
        ),
        status=assignment_status,
    )

    try:
        return save_assignment(assignment)

    except Exception:
        db.session.rollback()
        raise


def _validate_assignment_manager(
    assignment,
    actor_user_id,
    actor_role,
):
    _validate_offering_manager(
        assignment.offering,
        actor_user_id,
        actor_role,
    )


def update_assignment(
    assignment_id,
    data,
    actor_user_id,
    actor_role,
):
    if not data:
        raise AssignmentValidationError(
            "At least one field must be provided for an update."
        )

    assignment = _get_assignment_or_404(
        assignment_id
    )

    _validate_assignment_manager(
        assignment,
        actor_user_id,
        actor_role,
    )

    if assignment.status == "CLOSED":
        raise AssignmentValidationError(
            "A CLOSED assignment cannot be modified."
        )

    available_from = data.get(
        "available_from",
        assignment.available_from,
    )

    due_at = data.get(
        "due_at",
        assignment.due_at,
    )

    available_from, due_at = _validate_assignment_dates(
        available_from,
        due_at,
    )

    if "max_marks" in data:
        data["max_marks"] = _validate_max_marks(
            data["max_marks"]
        )

    if "title" in data:
        title = data["title"].strip()

        if len(title) < 3:
            raise AssignmentValidationError(
                "Assignment title must contain at least 3 non-whitespace characters."
            )

        data["title"] = title

    if assignment.submissions:
        if "max_marks" in data:
            existing_highest_marks = max(
                (
                    Decimal(str(submission.marks_obtained))
                    for submission in assignment.submissions
                    if submission.marks_obtained is not None
                ),
                default=Decimal("0"),
            )

            if data["max_marks"] < existing_highest_marks:
                raise AssignmentValidationError(
                    "Maximum marks cannot be lower than marks already awarded."
                )

        if due_at < assignment.due_at:
            raise AssignmentValidationError(
                "Due date cannot be moved earlier after submissions have been received."
            )

    for field in (
        "title",
        "description",
        "instructions",
        "max_marks",
        "allow_late_submissions",
        "allow_resubmissions",
    ):
        if field in data:
            setattr(
                assignment,
                field,
                data[field],
            )

    assignment.available_from = available_from
    assignment.due_at = due_at

    try:
        commit_changes()
        return assignment

    except Exception:
        db.session.rollback()
        raise


def change_assignment_status(
    assignment_id,
    status,
    actor_user_id,
    actor_role,
):
    assignment = _get_assignment_or_404(
        assignment_id
    )

    _validate_assignment_manager(
        assignment,
        actor_user_id,
        actor_role,
    )

    if assignment.status == "CLOSED" and status != "CLOSED":
        raise AssignmentValidationError(
            "A CLOSED assignment cannot be reopened."
        )

    if (
        status == "PUBLISHED"
        and assignment.offering.status != "OPEN"
    ):
        raise AssignmentValidationError(
            "An assignment can be published only for an OPEN course offering."
        )

    if (
        assignment.status == "PUBLISHED"
        and status == "DRAFT"
        and assignment.submissions
    ):
        raise AssignmentValidationError(
            "An assignment with submissions cannot be moved back to DRAFT."
        )

    assignment.status = status

    try:
        commit_changes()
        return assignment

    except Exception:
        db.session.rollback()
        raise


def delete_assignment(
    assignment_id,
    actor_user_id,
    actor_role,
):
    assignment = _get_assignment_or_404(
        assignment_id
    )

    _validate_assignment_manager(
        assignment,
        actor_user_id,
        actor_role,
    )

    if assignment.submissions:
        raise AssignmentConflictError(
            "An assignment with submissions cannot be deleted. Close it instead."
        )

    try:
        db.session.delete(assignment)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        raise


def _get_student_enrollment(
    student_id,
    offering_id,
):
    return db.session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.offering_id == offering_id,
            Enrollment.status == "ENROLLED",
        )
    )


def get_assignment_for_user(
    assignment_id,
    actor_user_id,
    actor_role,
):
    assignment = _get_assignment_or_404(
        assignment_id
    )

    if actor_role in {"ADMIN", "FACULTY"}:
        _validate_assignment_manager(
            assignment,
            actor_user_id,
            actor_role,
        )

        return assignment

    if actor_role == "STUDENT":
        student = _student_for_user(
            actor_user_id
        )

        if student is None:
            raise AssignmentAccessDeniedError(
                "Student profile was not found."
            )

        enrolled = _get_student_enrollment(
            student.id,
            assignment.offering_id,
        )

        if enrolled is None or assignment.status != "PUBLISHED":
            raise AssignmentAccessDeniedError(
                "You cannot access this assignment."
            )

        return assignment

    raise AssignmentAccessDeniedError(
        "You are not authorized to view this assignment."
    )


def list_assignments_for_user(
    actor_user_id,
    actor_role,
    page=1,
    per_page=10,
    offering_id=None,
    status=None,
):
    faculty_id = None

    if actor_role == "FACULTY":
        faculty = _faculty_for_user(
            actor_user_id
        )

        if faculty is None:
            raise AssignmentAccessDeniedError(
                "Faculty profile was not found."
            )

        faculty_id = faculty.id

    elif actor_role != "ADMIN":
        raise AssignmentAccessDeniedError(
            "You are not authorized to list assignments."
        )

    return list_assignments_paginated(
        page=page,
        per_page=per_page,
        offering_id=offering_id,
        status=status,
        faculty_id=faculty_id,
    )


def list_my_assignments(
    actor_user_id,
    page=1,
    per_page=10,
    offering_id=None,
):
    student = _student_for_user(
        actor_user_id
    )

    if student is None:
        raise AssignmentAccessDeniedError(
            "Student profile was not found."
        )

    return list_student_assignments_paginated(
        student_id=student.id,
        page=page,
        per_page=per_page,
        offering_id=offering_id,
    )


def _submission_window(assignment, student):
    if assignment.status != "PUBLISHED":
        raise AssignmentValidationError(
            "Only PUBLISHED assignments can be submitted."
        )

    if _get_student_enrollment(
        student.id,
        assignment.offering_id,
    ) is None:
        raise AssignmentAccessDeniedError(
            "You can submit assignments only for your enrolled course offerings."
        )

    now = _now()

    if now < assignment.available_from:
        raise AssignmentValidationError(
            "This assignment is not available yet."
        )

    is_late = now > assignment.due_at

    if is_late and not assignment.allow_late_submissions:
        raise AssignmentValidationError(
            "The submission deadline has passed."
        )

    return now, is_late


def _read_assignment_pdf(upload):
    filename = secure_filename(upload.filename or "")

    if not filename or not filename.lower().endswith(".pdf"):
        raise AssignmentValidationError(
            "A PDF file with a .pdf filename is required."
        )

    max_bytes = current_app.config["ASSIGNMENT_PDF_MAX_BYTES"]
    content = upload.stream.read(max_bytes + 1)

    if len(content) > max_bytes:
        raise AssignmentValidationError(
            f"PDF files cannot exceed {max_bytes} bytes."
        )

    if not content or b"%PDF-" not in content[:1024]:
        raise AssignmentValidationError(
            "The uploaded file does not have a valid PDF header."
        )

    return filename, content


def _delete_pdf_object(object_key):
    if object_key is None:
        return

    try:
        delete_pdf(object_key)
    except AssignmentStorageError:
        current_app.logger.exception(
            "Could not remove assignment PDF object %s.",
            object_key,
        )


def submit_pdf_assignment(
    assignment_id,
    upload,
    actor_user_id,
):
    assignment = _get_assignment_or_404(assignment_id)
    student = _student_for_user(actor_user_id)

    if student is None:
        raise AssignmentAccessDeniedError(
            "Student profile was not found."
        )

    now, is_late = _submission_window(assignment, student)

    existing = get_submission_by_assignment_student(
        assignment.id,
        student.id,
    )

    if existing is not None:
        raise AssignmentConflictError(
            "A submission already exists. Use the resubmission endpoint if enabled."
        )

    filename, content = _read_assignment_pdf(upload)
    submission_id = uuid4()
    object_key = (
        f"assignment-submissions/{assignment.id}/"
        f"{student.id}/{submission_id}.pdf"
    )

    store_pdf(object_key, content)

    submission = AssignmentSubmission(
        id=submission_id,
        assignment_id=assignment.id,
        student_id=student.id,
        pdf_object_key=object_key,
        pdf_filename=filename,
        submitted_at=now,
        is_late=is_late,
        resubmission_count=0,
        status="SUBMITTED",
    )

    try:
        return save_submission(submission)

    except IntegrityError as exc:
        db.session.rollback()
        _delete_pdf_object(object_key)

        raise AssignmentConflictError(
            "A submission already exists for this assignment."
        ) from exc

    except Exception:
        db.session.rollback()
        _delete_pdf_object(object_key)
        raise


def resubmit_pdf_assignment(
    submission_id,
    upload,
    actor_user_id,
):
    submission = get_submission_by_id(submission_id)

    if submission is None:
        raise SubmissionNotFoundError(
            "Assignment submission not found."
        )

    student = _student_for_user(actor_user_id)

    if student is None or submission.student_id != student.id:
        raise AssignmentAccessDeniedError(
            "You can update only your own submission."
        )

    assignment = submission.assignment

    if _get_student_enrollment(
        student.id,
        assignment.offering_id,
    ) is None:
        raise AssignmentAccessDeniedError(
            "You can resubmit assignments only for your enrolled course offerings."
        )

    if not assignment.allow_resubmissions:
        raise AssignmentValidationError(
            "Resubmissions are not allowed for this assignment."
        )

    if submission.status == "GRADED":
        raise AssignmentValidationError(
            "A graded submission cannot be resubmitted."
        )

    now, is_late = _submission_window(assignment, student)
    filename, content = _read_assignment_pdf(upload)
    object_key = (
        f"assignment-submissions/{assignment.id}/"
        f"{student.id}/{uuid4()}.pdf"
    )

    store_pdf(object_key, content)

    previous_pdf_key = submission.pdf_object_key
    submission.pdf_object_key = object_key
    submission.pdf_filename = filename
    submission.submitted_at = now
    submission.is_late = is_late
    submission.resubmission_count += 1

    try:
        commit_changes()
    except Exception:
        db.session.rollback()
        _delete_pdf_object(object_key)
        raise

    _delete_pdf_object(previous_pdf_key)
    return submission


def get_pdf_download_url(
    submission_id,
    actor_user_id,
    actor_role,
):
    submission = get_submission_for_user(
        submission_id,
        actor_user_id,
        actor_role,
    )

    if not submission.pdf_object_key or not submission.pdf_filename:
        raise AssignmentFileNotFoundError(
            "This submission does not have a PDF file."
        )

    return create_pdf_download_url(
        submission.pdf_object_key,
        submission.pdf_filename,
    )


def list_assignment_submissions(
    assignment_id,
    actor_user_id,
    actor_role,
    page=1,
    per_page=10,
    status=None,
):
    assignment = _get_assignment_or_404(
        assignment_id
    )

    _validate_assignment_manager(
        assignment,
        actor_user_id,
        actor_role,
    )

    return list_submissions_paginated(
        assignment_id=assignment.id,
        page=page,
        per_page=per_page,
        status=status,
    )


def get_submission_for_user(
    submission_id,
    actor_user_id,
    actor_role,
):
    submission = get_submission_by_id(
        submission_id
    )

    if submission is None:
        raise SubmissionNotFoundError(
            "Assignment submission not found."
        )

    if actor_role in {"ADMIN", "FACULTY"}:
        _validate_assignment_manager(
            submission.assignment,
            actor_user_id,
            actor_role,
        )

        return submission

    if actor_role == "STUDENT":
        student = _student_for_user(
            actor_user_id
        )

        if student is None or submission.student_id != student.id:
            raise AssignmentAccessDeniedError(
                "You can access only your own assignment submissions."
            )

        return submission

    raise AssignmentAccessDeniedError(
        "You are not authorized to view this submission."
    )


def grade_submission(
    submission_id,
    data,
    actor_user_id,
    actor_role,
):
    actor_user_id = _normalize_user_id(
        actor_user_id
    )

    submission = get_submission_by_id(
        submission_id
    )

    if submission is None:
        raise SubmissionNotFoundError(
            "Assignment submission not found."
        )

    _validate_assignment_manager(
        submission.assignment,
        actor_user_id,
        actor_role,
    )

    marks = Decimal(
        str(data["marks_obtained"])
    )

    if not marks.is_finite() or marks < 0:
        raise AssignmentValidationError(
            "Marks must be a finite non-negative number."
        )

    if marks.as_tuple().exponent < -2:
        raise AssignmentValidationError(
            "Marks can have at most two decimal places."
        )

    if marks > Decimal("999999.99"):
        raise AssignmentValidationError(
            "Marks cannot exceed 999999.99."
        )

    maximum_marks = Decimal(
        str(submission.assignment.max_marks)
    )

    if marks > maximum_marks:
        raise AssignmentValidationError(
            f"Marks cannot exceed maximum marks ({maximum_marks})."
        )

    submission.marks_obtained = marks
    submission.feedback = data.get("feedback")
    submission.graded_by = actor_user_id
    submission.graded_at = _now()
    submission.status = "GRADED"

    try:
        commit_changes()
        return submission

    except Exception:
        db.session.rollback()
        raise
