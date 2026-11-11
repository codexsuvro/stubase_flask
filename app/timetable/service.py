from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound, Forbidden, Conflict, UnprocessableEntity
from app.extensions import db
from app.models.course_offering import CourseOffering
from app.models.faculty import Faculty
from app.models.semester import Semester
from app.timetable.models import Classroom, TimetableSlot
from app.timetable.repository import (
    get_classroom_by_id,
    get_classroom_by_location,
    list_classrooms,
    get_slot_by_id,
    list_slots,
    find_conflicting_slots,
)


class TimetableValidationError(Exception):
    pass


class TimetableConflictError(Exception):
    pass


class TimetablePermissionError(Exception):
    pass


def _lock_resources(keys):
    """
    Serialize timetable writes for the same faculty, room,
    offering and weekday. PostgreSQL transaction-level locks.
    """
    for key in sorted(set(keys)):
        db.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key": key},
        )


def _get_faculty_for_user(user_id):
    faculty = db.session.query(Faculty).filter_by(
        user_id=user_id
    ).first()

    if faculty is None:
        raise NotFound("Faculty profile not found.")

    return faculty


def create_classroom(data):
    building = data["building"].strip()
    room_number = data["room_number"].strip().upper()

    if not building or not room_number:
        raise TimetableValidationError(
            "Building and room number cannot be blank."
        )

    if get_classroom_by_location(building, room_number):
        raise TimetableConflictError(
            "A classroom with this building and room number already exists."
        )

    classroom = Classroom(
        building=building,
        room_number=room_number,
        capacity=data["capacity"],
        room_type=data.get("room_type", "CLASSROOM"),
        status="ACTIVE",
    )

    try:
        db.session.add(classroom)
        db.session.commit()
        return classroom

    except IntegrityError as exc:
        db.session.rollback()
        raise TimetableConflictError(
            "A classroom with this building and room number already exists."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def get_classroom(classroom_id):
    classroom = get_classroom_by_id(classroom_id)

    if classroom is None:
        raise NotFound("Classroom not found.")

    return classroom


def get_all_classrooms(status=None):
    return list_classrooms(status=status)


def update_classroom(classroom_id, data):
    classroom = get_classroom(classroom_id)

    new_building = data.get("building", classroom.building).strip()
    new_room_number = data.get(
        "room_number",
        classroom.room_number,
    ).strip().upper()

    if not new_building or not new_room_number:
        raise TimetableValidationError(
            "Building and room number cannot be blank."
        )

    existing = get_classroom_by_location(
        new_building,
        new_room_number,
    )

    if existing and existing.id != classroom.id:
        raise TimetableConflictError(
            "A classroom with this building and room number already exists."
        )

    new_capacity = data.get("capacity", classroom.capacity)

    if new_capacity < classroom.capacity:
        # Do not reduce a room below the capacity of an assigned offering.
        for slot in classroom.timetable_slots:
            if (
                slot.status == "ACTIVE"
                and slot.offering.capacity > new_capacity
            ):
                raise TimetableValidationError(
                    "Classroom capacity cannot be lower than "
                    "the capacity of an assigned course offering."
                )

    if data.get("status") == "INACTIVE":
        active_slots = [
            slot for slot in classroom.timetable_slots
            if slot.status == "ACTIVE"
        ]

        if active_slots:
            raise TimetableValidationError(
                "A classroom with active timetable slots cannot be deactivated."
            )

    classroom.building = new_building
    classroom.room_number = new_room_number
    classroom.capacity = new_capacity
    classroom.room_type = data.get(
        "room_type",
        classroom.room_type,
    )
    classroom.status = data.get(
        "status",
        classroom.status,
    )

    try:
        db.session.commit()
        return classroom

    except IntegrityError as exc:
        db.session.rollback()
        raise TimetableConflictError(
            "Classroom update conflicts with an existing record."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def _validate_slot_data(data, offering, classroom):
    semester = offering.semester

    
    if offering.status != "OPEN":
        raise TimetableValidationError(
            "Timetable can be created or modified only for OPEN offerings."
        )


    if semester.status != "ACTIVE":
        raise TimetableValidationError(
            "Timetable can be managed only for an ACTIVE semester."
        )

    if semester.academic_year.status != "ACTIVE":
        raise TimetableValidationError(
            "The academic year must be ACTIVE to manage its timetable."
        )

    if classroom.status != "ACTIVE":
        raise TimetableValidationError(
            "An INACTIVE classroom cannot be scheduled."
        )

    if classroom.capacity < offering.capacity:
        raise TimetableValidationError(
            "Classroom capacity cannot be lower than course offering capacity."
        )

    if data["effective_from"] < semester.start_date:
        raise TimetableValidationError(
            "Timetable start date cannot be before the semester start date."
        )

    if data["effective_until"] > semester.end_date:
        raise TimetableValidationError(
            "Timetable end date cannot be after the semester end date."
        )

    if data["effective_from"] > data["effective_until"]:
        raise TimetableValidationError(
            "Effective until must be on or after effective from."
        )

    if data["start_time"] >= data["end_time"]:
        raise TimetableValidationError(
            "End time must be after start time."
        )


def _check_conflicts(data, offering, faculty_id, classroom_id, exclude_id=None):
    conflicts = find_conflicting_slots(
        day_of_week=data["day_of_week"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        effective_from=data["effective_from"],
        effective_until=data["effective_until"],
        exclude_slot_id=exclude_id,
    )

    for existing in conflicts:

        if existing.offering_id == offering.id:
            raise TimetableConflictError(
                "This course offering already has an overlapping "
                "timetable slot on this day."
            )

        if existing.faculty_id == faculty_id:
            raise TimetableConflictError(
                "Faculty member already has a class during this time."
            )

        if existing.classroom_id == classroom_id:
            raise TimetableConflictError(
                "Classroom is already occupied during this time."
            )


def create_timetable_slot(data, user_id):
    offering = db.session.get(
        CourseOffering,
        data["offering_id"],
    )

    if offering is None:
        raise NotFound("Course offering not found.")

    classroom = get_classroom(data["classroom_id"])

    faculty_id = offering.faculty_id

    _validate_slot_data(data, offering, classroom)

    _lock_resources([
        f"faculty:{faculty_id}:day:{data['day_of_week']}",
        f"classroom:{classroom.id}:day:{data['day_of_week']}",
        f"offering:{offering.id}:day:{data['day_of_week']}",
    ])

    _check_conflicts(
        data,
        offering,
        faculty_id,
        classroom.id,
    )

    slot = TimetableSlot(
        offering_id=offering.id,
        faculty_id=faculty_id,
        classroom_id=classroom.id,
        day_of_week=data["day_of_week"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        effective_from=data["effective_from"],
        effective_until=data["effective_until"],
        session_type=data.get("session_type", "LECTURE"),
        remarks=data.get("remarks"),
        status="ACTIVE",
    )

    try:
        db.session.add(slot)
        db.session.commit()
        return get_slot_by_id(slot.id)

    except IntegrityError as exc:
        db.session.rollback()
        raise TimetableConflictError(
            "Timetable slot conflicts with an existing record."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def get_timetable_slot(slot_id, user_id=None):
    slot = get_slot_by_id(slot_id)

    if slot is None:
        raise NotFound("Timetable slot not found.")

    if user_id is not None:
        faculty = _get_faculty_for_user(user_id)

        if slot.faculty_id != faculty.id:
            raise Forbidden(
                "You can view only timetable slots assigned to you."
            )

    return slot


def get_all_timetable_slots(filters, user_id=None):
    if user_id is not None:
        faculty = _get_faculty_for_user(user_id)
        filters["faculty_id"] = faculty.id

    return list_slots(**filters)


def update_timetable_slot(slot_id, data):
    slot = get_slot_by_id(slot_id)

    if slot is None:
        raise NotFound("Timetable slot not found.")

    if slot.status == "CANCELLED":
        raise TimetableValidationError(
            "A CANCELLED timetable slot cannot be modified."
        )

    offering = slot.offering

    if offering.semester.status != "ACTIVE":
        raise TimetableValidationError(
            "Timetable can be modified only during an ACTIVE semester."
        )

    classroom_id = data.get("classroom_id", slot.classroom_id)
    classroom = get_classroom(classroom_id)

    merged = {
        "day_of_week": data.get(
            "day_of_week",
            slot.day_of_week,
        ),
        "start_time": data.get(
            "start_time",
            slot.start_time,
        ),
        "end_time": data.get(
            "end_time",
            slot.end_time,
        ),
        "effective_from": data.get(
            "effective_from",
            slot.effective_from,
        ),
        "effective_until": data.get(
            "effective_until",
            slot.effective_until,
        ),
    }

    _validate_slot_data(merged, offering, classroom)

    _lock_resources([
        f"faculty:{slot.faculty_id}:day:{merged['day_of_week']}",
        f"classroom:{classroom.id}:day:{merged['day_of_week']}",
        f"offering:{offering.id}:day:{merged['day_of_week']}",
    ])

    _check_conflicts(
        merged,
        offering,
        slot.faculty_id,
        classroom.id,
        exclude_id=slot.id,
    )

    slot.classroom_id = classroom.id
    slot.day_of_week = merged["day_of_week"]
    slot.start_time = merged["start_time"]
    slot.end_time = merged["end_time"]
    slot.effective_from = merged["effective_from"]
    slot.effective_until = merged["effective_until"]
    slot.session_type = data.get(
        "session_type",
        slot.session_type,
    )
    slot.remarks = data.get("remarks", slot.remarks)

    try:
        db.session.commit()
        return get_slot_by_id(slot.id)

    except IntegrityError as exc:
        db.session.rollback()
        raise TimetableConflictError(
            "Timetable update conflicts with an existing record."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


def cancel_timetable_slot(slot_id):
    slot = get_slot_by_id(slot_id)

    if slot is None:
        raise NotFound("Timetable slot not found.")

    if slot.status == "CANCELLED":
        raise TimetableValidationError(
            "Timetable slot is already CANCELLED."
        )

    slot.status = "CANCELLED"

    try:
        db.session.commit()
        return slot

    except Exception:
        db.session.rollback()
        raise
