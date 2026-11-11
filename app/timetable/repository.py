from sqlalchemy import select, and_
from app.extensions import db
from app.timetable.models import Classroom, TimetableSlot


def get_classroom_by_id(classroom_id):
    return db.session.get(Classroom, classroom_id)


def get_classroom_by_location(building, room_number):
    statement = select(Classroom).where(
        Classroom.building == building,
        Classroom.room_number == room_number,
    )
    return db.session.scalar(statement)


def list_classrooms(status=None):
    statement = select(Classroom).order_by(
        Classroom.building,
        Classroom.room_number,
    )

    if status:
        statement = statement.where(
            Classroom.status == status
        )

    return db.session.scalars(statement).all()


def get_slot_by_id(slot_id):
    return db.session.get(TimetableSlot, slot_id)


def list_slots(
    offering_id=None,
    faculty_id=None,
    classroom_id=None,
    semester_id=None,
    day_of_week=None,
    status="ACTIVE",
):
    statement = (
        select(TimetableSlot)
        .join(
            TimetableSlot.offering
        )
        .order_by(
            TimetableSlot.day_of_week,
            TimetableSlot.start_time,
        )
    )

    if offering_id:
        statement = statement.where(
            TimetableSlot.offering_id == offering_id
        )

    if faculty_id:
        statement = statement.where(
            TimetableSlot.faculty_id == faculty_id
        )

    if classroom_id:
        statement = statement.where(
            TimetableSlot.classroom_id == classroom_id
        )

    if semester_id:
        statement = statement.where(
            TimetableSlot.offering.has(
                semester_id=semester_id
            )
        )

    if day_of_week:
        statement = statement.where(
            TimetableSlot.day_of_week == day_of_week
        )

    if status:
        statement = statement.where(
            TimetableSlot.status == status
        )

    return db.session.scalars(statement).unique().all()


def find_conflicting_slots(
    day_of_week,
    start_time,
    end_time,
    effective_from,
    effective_until,
    exclude_slot_id=None,
):
    statement = select(TimetableSlot).where(
        TimetableSlot.status == "ACTIVE",
        TimetableSlot.day_of_week == day_of_week,

        # Time intervals overlap.
        TimetableSlot.start_time < end_time,
        TimetableSlot.end_time > start_time,

        # Effective date ranges overlap.
        TimetableSlot.effective_from <= effective_until,
        TimetableSlot.effective_until >= effective_from,
    )

    if exclude_slot_id:
        statement = statement.where(
            TimetableSlot.id != exclude_slot_id
        )

    return db.session.scalars(statement).all()


def get_slots_for_offering(offering_id):
    statement = select(TimetableSlot).where(
        TimetableSlot.offering_id == offering_id,
        TimetableSlot.status == "ACTIVE",
    )

    return db.session.scalars(statement).all()
