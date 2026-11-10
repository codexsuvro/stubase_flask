import re
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.academic_year import AcademicYear
from app.models.semester import Semester
from app.academic_calendar.repository import (
    get_academic_year_by_id,
    get_academic_year_by_name,
    list_academic_years,
    get_semester_by_id,
    get_semester_by_number,
    list_semesters,
)


# ==========================================================
# CUSTOM EXCEPTIONS
# ==========================================================

class AcademicYearNotFoundError(Exception):
    pass


class AcademicYearAlreadyExistsError(Exception):
    pass


class SemesterNotFoundError(Exception):
    pass


class SemesterAlreadyExistsError(Exception):
    pass


class InvalidAcademicCalendarError(Exception):
    pass


class ActiveAcademicYearExistsError(Exception):
    pass


class ActiveSemesterExistsError(Exception):
    pass


# ==========================================================
# CONSTANTS
# ==========================================================

VALID_STATUSES = {"PLANNED", "ACTIVE", "COMPLETED"}


# ==========================================================
# BASIC VALIDATION HELPERS
# ==========================================================

def validate_status(status):
    if status not in VALID_STATUSES:
        raise ValueError(
            "Status must be PLANNED, ACTIVE, or COMPLETED."
        )


def validate_academic_year_name(name):
    """Validate the YYYY-YYYY format and consecutive years."""
    name = name.strip()

    if not re.fullmatch(r"\d{4}-\d{4}", name):
        raise ValueError(
            "Academic year must follow YYYY-YYYY format."
        )

    start_year, end_year = map(int, name.split("-"))

    if end_year != start_year + 1:
        raise ValueError(
            "Academic year must contain consecutive years."
        )

    return name


def validate_academic_year_dates(start_date, end_date):
    if start_date >= end_date:
        raise ValueError(
            "Academic year end date must be after start date."
        )


def validate_semester_dates(academic_year, start_date, end_date):
    if start_date >= end_date:
        raise ValueError(
            "Semester end date must be after start date."
        )

    if (
        start_date < academic_year.start_date
        or end_date > academic_year.end_date
    ):
        raise InvalidAcademicCalendarError(
            "Semester dates must fall within the academic year date range."
        )


def validate_semester_name(semester_name):
    """Strip whitespace and prevent blank semester names."""
    semester_name = semester_name.strip()

    if not semester_name:
        raise ValueError("Semester name cannot be blank.")

    return semester_name


# ==========================================================
# STATUS-CONSISTENCY VALIDATION
# ==========================================================

def get_semester_statuses(academic_year):
    return {semester.status for semester in academic_year.semesters}


def validate_academic_year_status_transition(academic_year, new_status):
    """
    Enforce consistency between an academic year and its semesters.

    PLANNED year:
        May contain only PLANNED semesters.

    ACTIVE year:
        May contain PLANNED, ACTIVE, or COMPLETED semesters.

    COMPLETED year:
        May contain only COMPLETED semesters.
    """
    semester_statuses = get_semester_statuses(academic_year)

    # A completed academic year is terminal and cannot be reopened.
    if academic_year.status == "COMPLETED" and new_status != "COMPLETED":
        raise InvalidAcademicCalendarError(
            "A COMPLETED academic year cannot be reopened."
        )

    if new_status == "PLANNED":
        if semester_statuses.intersection({"ACTIVE", "COMPLETED"}):
            raise InvalidAcademicCalendarError(
                "An academic year cannot be PLANNED while it contains "
                "an ACTIVE or COMPLETED semester."
            )

    elif new_status == "COMPLETED":
        if semester_statuses.intersection({"PLANNED", "ACTIVE"}):
            raise InvalidAcademicCalendarError(
                "All semesters must be COMPLETED before completing "
                "the academic year."
            )


def validate_semester_status_transition(semester, new_status):
    academic_year = semester.academic_year

    if new_status in {"ACTIVE", "COMPLETED"}:
        if academic_year.status == "PLANNED":
            raise InvalidAcademicCalendarError(
                "The academic year must be ACTIVE before a semester "
                "can become ACTIVE or COMPLETED."
            )

    if academic_year.status == "COMPLETED" and new_status != "COMPLETED":
        raise InvalidAcademicCalendarError(
            "A semester under a COMPLETED academic year cannot be "
            "changed to PLANNED or ACTIVE."
        )
        
    if semester.status == "COMPLETED" and new_status != "COMPLETED":
        raise InvalidAcademicCalendarError(
            "A COMPLETED semester cannot be reopened."
        )


# ==========================================================
# ACTIVE RESOURCE VALIDATION
# ==========================================================

def ensure_no_other_active_academic_year(exclude_id=None):
    statement = select(AcademicYear).where(
        AcademicYear.status == "ACTIVE"
    )

    if exclude_id is not None:
        statement = statement.where(AcademicYear.id != exclude_id)

    if db.session.scalar(statement) is not None:
        raise ActiveAcademicYearExistsError(
            "Another academic year is already ACTIVE."
        )


def ensure_no_other_active_semester(academic_year_id, exclude_id=None):
    statement = select(Semester).where(
        Semester.academic_year_id == academic_year_id,
        Semester.status == "ACTIVE",
    )

    if exclude_id is not None:
        statement = statement.where(Semester.id != exclude_id)

    if db.session.scalar(statement) is not None:
        raise ActiveSemesterExistsError(
            "Another semester is already ACTIVE in this academic year."
        )


def ensure_no_overlapping_semester_dates(
    academic_year_id,
    start_date,
    end_date,
    exclude_id=None,
):
    statement = select(Semester).where(
        Semester.academic_year_id == academic_year_id,
        Semester.start_date < end_date,
        Semester.end_date > start_date,
    )

    if exclude_id is not None:
        statement = statement.where(Semester.id != exclude_id)

    if db.session.scalar(statement) is not None:
        raise InvalidAcademicCalendarError(
            "Semester date range overlaps with another semester "
            "in this academic year."
        )


# ==========================================================
# ACADEMIC YEAR OPERATIONS
# ==========================================================

def create_academic_year(data):
    name = validate_academic_year_name(data["name"])
    start_date = data["start_date"]
    end_date = data["end_date"]
    status = data.get("status", "PLANNED")

    validate_status(status)
    validate_academic_year_dates(start_date, end_date)

    if get_academic_year_by_name(name):
        raise AcademicYearAlreadyExistsError(
            "Academic year already exists."
        )

    if status == "ACTIVE":
        ensure_no_other_active_academic_year()

    academic_year = AcademicYear(
        name=name,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )

    try:
        db.session.add(academic_year)
        db.session.commit()
        return academic_year

    except IntegrityError as exc:
        db.session.rollback()
        raise AcademicYearAlreadyExistsError(
            "Academic year already exists."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def get_academic_year(academic_year_id):
    academic_year = get_academic_year_by_id(academic_year_id)

    if academic_year is None:
        raise AcademicYearNotFoundError("Academic year not found.")

    return academic_year


def get_all_academic_years():
    return list_academic_years()


def update_academic_year(academic_year_id, data):
    academic_year = get_academic_year(academic_year_id)

    new_name = data.get("name", academic_year.name)

    if "name" in data:
        new_name = validate_academic_year_name(new_name)
        existing = get_academic_year_by_name(new_name)

        if existing and existing.id != academic_year.id:
            raise AcademicYearAlreadyExistsError(
                "Academic year name is already in use."
            )

    start_date = data.get("start_date", academic_year.start_date)
    end_date = data.get("end_date", academic_year.end_date)

    validate_academic_year_dates(start_date, end_date)

    for semester in academic_year.semesters:
        if (
            semester.start_date < start_date
            or semester.end_date > end_date
        ):
            raise InvalidAcademicCalendarError(
                "Updated academic year dates cannot exclude "
                "an existing semester."
            )

    try:
        academic_year.name = new_name
        academic_year.start_date = start_date
        academic_year.end_date = end_date
        db.session.commit()
        return academic_year

    except IntegrityError as exc:
        db.session.rollback()
        raise AcademicYearAlreadyExistsError(
            "Academic year name is already in use."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def update_academic_year_status(academic_year_id, status):
    validate_status(status)
    academic_year = get_academic_year(academic_year_id)

    if status == "ACTIVE":
        ensure_no_other_active_academic_year(
            exclude_id=academic_year.id
        )

    validate_academic_year_status_transition(academic_year, status)

    try:
        academic_year.status = status
        db.session.commit()
        return academic_year

    except Exception:
        db.session.rollback()
        raise


# ==========================================================
# SEMESTER OPERATIONS
# ==========================================================

def create_semester(data):
    academic_year = get_academic_year(data["academic_year_id"])

    semester_number = data["semester_number"]
    semester_name = validate_semester_name(data["semester_name"])
    start_date = data["start_date"]
    end_date = data["end_date"]
    status = data.get("status", "PLANNED")

    validate_status(status)

    if get_semester_by_number(academic_year.id, semester_number):
        raise SemesterAlreadyExistsError(
            "This semester number already exists in the academic year."
        )

    if academic_year.status == "COMPLETED":
        raise InvalidAcademicCalendarError(
            "Cannot create a semester under a completed academic year."
        )

    if academic_year.status == "PLANNED" and status != "PLANNED":
        raise InvalidAcademicCalendarError(
            "A semester under a PLANNED academic year must remain PLANNED."
        )

    validate_semester_dates(academic_year, start_date, end_date)

    ensure_no_overlapping_semester_dates(
        academic_year.id,
        start_date,
        end_date,
    )

    if status == "ACTIVE":
        if academic_year.status != "ACTIVE":
            raise InvalidAcademicCalendarError(
                "The academic year must be ACTIVE before activating a semester."
            )
        ensure_no_other_active_semester(academic_year.id)

    semester = Semester(
        academic_year_id=academic_year.id,
        semester_number=semester_number,
        semester_name=semester_name,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )

    try:
        db.session.add(semester)
        db.session.commit()
        return semester

    except IntegrityError as exc:
        db.session.rollback()
        raise SemesterAlreadyExistsError(
            "This semester number already exists in the academic year."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def get_semester(semester_id):
    semester = get_semester_by_id(semester_id)

    if semester is None:
        raise SemesterNotFoundError("Semester not found.")

    return semester


def get_all_semesters(academic_year_id=None, status=None):
    if academic_year_id is not None:
        get_academic_year(academic_year_id)

    return list_semesters(
        academic_year_id=academic_year_id,
        status=status,
    )


def update_semester(semester_id, data):
    semester = get_semester(semester_id)
    academic_year = semester.academic_year

    if academic_year.status == "COMPLETED":
        raise InvalidAcademicCalendarError(
            "Semesters under a COMPLETED academic year cannot be modified."
        )

    semester_number = data.get(
        "semester_number",
        semester.semester_number,
    )

    existing = get_semester_by_number(
        academic_year.id,
        semester_number,
    )

    if existing and existing.id != semester.id:
        raise SemesterAlreadyExistsError(
            "This semester number already exists in the academic year."
        )

    semester_name = validate_semester_name(
        data.get("semester_name", semester.semester_name)
    )

    start_date = data.get("start_date", semester.start_date)
    end_date = data.get("end_date", semester.end_date)

    validate_semester_dates(academic_year, start_date, end_date)

    ensure_no_overlapping_semester_dates(
        academic_year.id,
        start_date,
        end_date,
        exclude_id=semester.id,
    )

    try:
        semester.semester_number = semester_number
        semester.semester_name = semester_name
        semester.start_date = start_date
        semester.end_date = end_date
        db.session.commit()
        return semester

    except IntegrityError as exc:
        db.session.rollback()
        raise SemesterAlreadyExistsError(
            "This semester number already exists in the academic year."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def update_semester_status(semester_id, status):
    validate_status(status)
    semester = get_semester(semester_id)
    academic_year = semester.academic_year

    validate_semester_status_transition(semester, status)

    if status == "ACTIVE":
        if academic_year.status != "ACTIVE":
            raise InvalidAcademicCalendarError(
                "The academic year must be ACTIVE before activating a semester."
            )

        ensure_no_other_active_semester(
            academic_year.id,
            exclude_id=semester.id,
        )

    try:
        semester.status = status
        db.session.commit()
        return semester

    except Exception:
        db.session.rollback()
        raise
