from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import (
    NotFound,
    Conflict,
    UnprocessableEntity,
)
from app.extensions import db
from app.faculty_workload.models import FacultyWorkloadPolicy
from app.faculty_workload.repository import (
    get_faculty_by_id,
    get_faculty_by_user_id,
    get_semester_by_id,
    get_faculty_slots,
    get_workload_policy,
    list_faculty,
    list_workload_policies,
    get_policy_by_id,
)


SESSION_TYPES = {
    "LECTURE",
    "PRACTICAL",
    "TUTORIAL",
    "SEMINAR",
}


def _round_hours(value):
    return Decimal(value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _slot_hours(slot):
    start_seconds = (
        slot.start_time.hour * 3600
        + slot.start_time.minute * 60
        + slot.start_time.second
    )

    end_seconds = (
        slot.end_time.hour * 3600
        + slot.end_time.minute * 60
        + slot.end_time.second
    )

    duration = end_seconds - start_seconds

    if duration <= 0:
        raise UnprocessableEntity(
            "Timetable slot has an invalid time duration."
        )

    return Decimal(duration) / Decimal(3600)


def _get_department_name(faculty):
    department = faculty.department

    if department is None:
        return "N/A"

    return (
        getattr(department, "department_name", None)
        or getattr(department, "name", None)
        or "N/A"
    )


def _get_course_code(course):
    if course is None:
        return "N/A"

    return (
        getattr(course, "course_code", None)
        or getattr(course, "code", None)
        or "N/A"
    )


def _get_course_name(course):
    if course is None:
        return "N/A"

    return (
        getattr(course, "course_name", None)
        or getattr(course, "name", None)
        or "N/A"
    )


def _validate_faculty_and_semester(faculty_id, semester_id):
    faculty = get_faculty_by_id(faculty_id)

    if faculty is None:
        raise NotFound("Faculty not found.")

    semester = get_semester_by_id(semester_id)

    if semester is None:
        raise NotFound("Semester not found.")

    return faculty, semester


def calculate_faculty_workload(faculty_id, semester_id):
    faculty, semester = _validate_faculty_and_semester(
        faculty_id,
        semester_id,
    )

    slots = get_faculty_slots(
        faculty_id,
        semester_id,
    )

    total_hours = Decimal("0")
    session_count = 0

    session_summary = {}
    course_summary = {}

    for slot in slots:
        hours = _slot_hours(slot)

        raw_session_type = (
            slot.session_type or "OTHER"
        ).upper()

        session_type = (
            raw_session_type
            if raw_session_type in SESSION_TYPES
            else "OTHER"
        )

        total_hours += hours
        session_count += 1

        if session_type not in session_summary:
            session_summary[session_type] = {
                "session_type": session_type,
                "total_sessions": 0,
                "weekly_hours": Decimal("0"),
            }

        session_summary[session_type]["total_sessions"] += 1
        session_summary[session_type]["weekly_hours"] += hours

        offering = slot.offering
        course = offering.course if offering else None

        course_key = (
            offering.id if offering else None,
            session_type,
        )

        if course_key not in course_summary:
            course_summary[course_key] = {
                "offering_id": (
                    offering.id if offering else None
                ),
                "course_code": _get_course_code(course),
                "course_name": _get_course_name(course),
                "section_code": (
                    getattr(offering, "section_code", None)
                    or "N/A"
                ),
                "session_type": session_type,
                "total_sessions": 0,
                "weekly_hours": Decimal("0"),
            }

        course_summary[course_key]["total_sessions"] += 1
        course_summary[course_key]["weekly_hours"] += hours

    total_hours = _round_hours(total_hours)

    breakdown = []

    for item in session_summary.values():
        item["weekly_hours"] = _round_hours(
            item["weekly_hours"]
        )
        breakdown.append(item)

    courses = []

    for item in course_summary.values():
        item["weekly_hours"] = _round_hours(
            item["weekly_hours"]
        )
        courses.append(item)

    breakdown.sort(
        key=lambda item: item["session_type"]
    )

    courses.sort(
        key=lambda item: (
            item["course_code"],
            item["section_code"],
            item["session_type"],
        )
    )

    policy = get_workload_policy(
        faculty_id,
        semester_id,
    )

    if policy is None:
        workload_status = "UNCONFIGURED"
        remaining_capacity = Decimal("0.00")

    else:
        if total_hours < policy.minimum_hours:
            workload_status = "UNDERLOADED"

        elif total_hours > policy.maximum_hours:
            workload_status = "OVERLOADED"

        else:
            workload_status = "WITHIN_LIMIT"

        remaining_capacity = _round_hours(
            policy.maximum_hours - total_hours
        )

    return {
        "faculty_id": faculty.id,
        "faculty_code": faculty.faculty_id,
        "faculty_name": (
            f"{faculty.first_name} {faculty.last_name}"
        ),
        "designation": faculty.designation,
        "department_name": _get_department_name(faculty),
        "semester_id": semester.id,
        "semester_name": semester.semester_name,
        "total_sessions": session_count,
        "weekly_teaching_hours": total_hours,
        "session_breakdown": breakdown,
        "courses": courses,
        "policy": policy,
        "workload_status": workload_status,
        "remaining_capacity_hours": remaining_capacity,
    }


def get_all_faculty_workloads(semester_id):
    semester = get_semester_by_id(semester_id)

    if semester is None:
        raise NotFound("Semester not found.")

    faculty_members = list_faculty()

    return [
        calculate_faculty_workload(
            faculty.id,
            semester_id,
        )
        for faculty in faculty_members
    ]


def get_faculty_workload_for_user(user_id, semester_id):
    faculty = get_faculty_by_user_id(user_id)

    if faculty is None:
        raise NotFound("Faculty profile not found.")

    return calculate_faculty_workload(
        faculty.id,
        semester_id,
    )


def create_workload_policy(data):
    faculty, semester = _validate_faculty_and_semester(
        data["faculty_id"],
        data["semester_id"],
    )

    minimum_hours = data.get(
        "minimum_hours",
        Decimal("0"),
    )

    maximum_hours = data["maximum_hours"]

    if minimum_hours > maximum_hours:
        raise UnprocessableEntity(
            "Minimum hours cannot exceed maximum hours."
        )

    existing = get_workload_policy(
        faculty.id,
        semester.id,
    )

    if existing is not None:
        raise Conflict(
            "A workload policy already exists for this faculty and semester."
        )

    current_workload = calculate_faculty_workload(
        faculty.id,
        semester.id,
    )

    if current_workload["weekly_teaching_hours"] > maximum_hours:
        raise UnprocessableEntity(
            "Maximum workload cannot be lower than the faculty's "
            "current scheduled teaching hours."
        )

    policy = FacultyWorkloadPolicy(
        faculty_id=faculty.id,
        semester_id=semester.id,
        minimum_hours=minimum_hours,
        maximum_hours=maximum_hours,
        remarks=data.get("remarks"),
    )

    try:
        db.session.add(policy)
        db.session.commit()
        return policy

    except IntegrityError as exc:
        db.session.rollback()
        raise Conflict(
            "A workload policy already exists for this faculty and semester."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def update_workload_policy(policy_id, data):
    policy = get_policy_by_id(policy_id)

    if policy is None:
        raise NotFound("Workload policy not found.")

    minimum_hours = data.get(
        "minimum_hours",
        policy.minimum_hours,
    )

    maximum_hours = data.get(
        "maximum_hours",
        policy.maximum_hours,
    )

    if minimum_hours > maximum_hours:
        raise UnprocessableEntity(
            "Minimum hours cannot exceed maximum hours."
        )

    current_workload = calculate_faculty_workload(
        policy.faculty_id,
        policy.semester_id,
    )

    if current_workload["weekly_teaching_hours"] > maximum_hours:
        raise UnprocessableEntity(
            "Maximum workload cannot be lower than the faculty's "
            "current scheduled teaching hours."
        )

    policy.minimum_hours = minimum_hours
    policy.maximum_hours = maximum_hours

    if "remarks" in data:
        policy.remarks = data["remarks"]

    try:
        db.session.commit()
        return policy

    except Exception:
        db.session.rollback()
        raise


def get_all_workload_policies(
    faculty_id=None,
    semester_id=None,
):
    if (
        faculty_id is not None
        and get_faculty_by_id(faculty_id) is None
    ):
        raise NotFound("Faculty not found.")

    if (
        semester_id is not None
        and get_semester_by_id(semester_id) is None
    ):
        raise NotFound("Semester not found.")

    return list_workload_policies(
        faculty_id=faculty_id,
        semester_id=semester_id,
    )