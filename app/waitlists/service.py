from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.student import Student
from app.models.course_offering import CourseOffering
from app.models.enrollment import Enrollment
from app.models.course_waitlist import CourseWaitlist

from app.waitlists.repository import (
    get_waitlist_entry,
    get_waitlist_by_id,
    list_waitlist_entries,
)

from app.course_prerequisites.service import (
    validate_student_prerequisites,
    InvalidCoursePrerequisiteError,
)


class WaitlistNotFoundError(Exception):
    pass


class WaitlistConflictError(Exception):
    pass


class InvalidWaitlistOperationError(Exception):
    pass


def _get_student_for_user(user_id):

    statement = select(Student).where(
        Student.user_id == user_id
    )

    student = db.session.scalar(statement)

    if student is None:
        raise WaitlistNotFoundError(
            "Student profile not found for this user."
        )

    return student


def _get_locked_offering(offering_id):

    statement = (
        select(CourseOffering)
        .where(CourseOffering.id == offering_id)
        .with_for_update()
    )

    offering = db.session.scalar(statement)

    if offering is None:
        raise WaitlistNotFoundError(
            "Course offering not found."
        )

    return offering


def _validate_offering_for_waitlist(offering):

    if offering.status != "OPEN":
        raise InvalidWaitlistOperationError(
            "Students can join the waitlist only for OPEN offerings."
        )

    if offering.semester.status != "ACTIVE":
        raise InvalidWaitlistOperationError(
            "Waitlist is available only for ACTIVE semesters."
        )

    if offering.semester.academic_year.status != "ACTIVE":
        raise InvalidWaitlistOperationError(
            "Waitlist is available only during an ACTIVE academic year."
        )


def _get_enrollment_count(offering_id):

    return db.session.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.offering_id == offering_id,
            Enrollment.status == "ENROLLED",
        )
    ) or 0


def join_waitlist(user_id, offering_id):

    student = _get_student_for_user(user_id)

    offering = _get_locked_offering(offering_id)

    _validate_offering_for_waitlist(offering)

    if student.department_id != offering.course.department_id:
        raise InvalidWaitlistOperationError(
            "Student and course must belong to the same department."
        )

    enrolled = db.session.scalar(
        select(Enrollment.id).where(
            Enrollment.student_id == student.id,
            Enrollment.offering_id == offering.id,
            Enrollment.status == "ENROLLED",
        ).limit(1)
    )

    if enrolled:
        raise WaitlistConflictError(
            "Student is already enrolled in this course offering."
        )

    enrollment_count = _get_enrollment_count(offering.id)

    if enrollment_count < offering.capacity:
        raise InvalidWaitlistOperationError(
            "Course offering still has available seats. "
            "Please enroll directly."
        )

    try:
        validate_student_prerequisites(
            student.id,
            offering.course_id,
        )

    except InvalidCoursePrerequisiteError as exc:
        raise InvalidWaitlistOperationError(str(exc)) from exc

    existing = get_waitlist_entry(
        student.id,
        offering.id,
    )

    if existing:

        if existing.status == "WAITING":
            raise WaitlistConflictError(
                "Student is already on the waitlist."
            )

        if existing.status == "PROMOTED":
            raise WaitlistConflictError(
                "Student has already been promoted."
            )

        # Reuse a cancelled/ineligible entry because the
        # student-offering pair is protected by a unique constraint.
        existing.status = "WAITING"
        existing.promoted_enrollment_id = None

        try:
            db.session.commit()
            return existing

        except Exception:
            db.session.rollback()
            raise

    waitlist_entry = CourseWaitlist(
        student_id=student.id,
        offering_id=offering.id,
        status="WAITING",
    )

    try:
        db.session.add(waitlist_entry)
        db.session.commit()
        db.session.refresh(waitlist_entry)

        return waitlist_entry

    except IntegrityError as exc:
        db.session.rollback()
        raise WaitlistConflictError(
            "Student is already registered for this offering's waitlist."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def get_my_waitlist(user_id):

    student = _get_student_for_user(user_id)

    return list_waitlist_entries(
        student_id=student.id
    )


def get_offering_waitlist(offering_id):

    offering = db.session.get(
        CourseOffering,
        offering_id,
    )

    if offering is None:
        raise WaitlistNotFoundError(
            "Course offering not found."
        )

    return list_waitlist_entries(
        offering_id=offering_id
    )


def cancel_waitlist_entry(waitlist_id, user_id=None):

    entry = get_waitlist_by_id(waitlist_id)

    if entry is None:
        raise WaitlistNotFoundError(
            "Waitlist entry not found."
        )

    if user_id is not None:

        student = _get_student_for_user(user_id)

        if entry.student_id != student.id:
            raise WaitlistNotFoundError(
                "Waitlist entry not found."
            )

    if entry.status != "WAITING":
        raise InvalidWaitlistOperationError(
            "Only WAITING entries can be cancelled."
        )

    entry.status = "CANCELLED"

    try:
        db.session.commit()
        return entry

    except Exception:
        db.session.rollback()
        raise


def promote_next_student(offering_id):

    offering = _get_locked_offering(offering_id)

    _validate_offering_for_waitlist(offering)

    enrollment_count = _get_enrollment_count(offering.id)

    if enrollment_count >= offering.capacity:
        raise InvalidWaitlistOperationError(
            "Course offering has no available seats."
        )

    statement = (
        select(CourseWaitlist)
        .where(
            CourseWaitlist.offering_id == offering.id,
            CourseWaitlist.status == "WAITING",
        )
        .order_by(
            CourseWaitlist.created_at.asc(),
            CourseWaitlist.id.asc(),
        )
        .with_for_update()
    )

    waiting_entries = db.session.scalars(statement).all()

    if not waiting_entries:
        raise WaitlistNotFoundError(
            "No students are currently waiting for this offering."
        )

    for entry in waiting_entries:

        try:
            validate_student_prerequisites(
                entry.student_id,
                offering.course_id,
            )

        except InvalidCoursePrerequisiteError:
            entry.status = "INELIGIBLE"
            continue

        enrollment = Enrollment(
            student_id=entry.student_id,
            course_id=offering.course_id,
            offering_id=offering.id,
            academic_year=offering.semester.academic_year.name,
            semester=offering.semester.semester_number,
            status="ENROLLED",
        )

        entry.status = "PROMOTED"

        db.session.add(enrollment)
        db.session.flush()

        entry.promoted_enrollment_id = enrollment.id

        try:
            db.session.commit()

            return {
                "message": "Student successfully promoted from waitlist.",
                "waitlist_id": entry.id,
                "enrollment_id": enrollment.id,
                "student_id": entry.student_id,
                "offering_id": offering.id,
            }

        except IntegrityError as exc:
            db.session.rollback()
            raise WaitlistConflictError(
                "Student could not be promoted because an enrollment "
                "conflict occurred."
            ) from exc

        except Exception:
            db.session.rollback()
            raise

    # All waiting students were ineligible.
    db.session.commit()

    raise InvalidWaitlistOperationError(
        "No eligible students are available for promotion."
    )