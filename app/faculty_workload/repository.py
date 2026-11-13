from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.faculty import Faculty
from app.models.semester import Semester
from app.models.course_offering import CourseOffering
from app.timetable.models import TimetableSlot
from app.faculty_workload.models import FacultyWorkloadPolicy


def get_faculty_by_id(faculty_id):
    return db.session.get(Faculty, faculty_id)


def get_faculty_by_user_id(user_id):
    statement = select(Faculty).where(
        Faculty.user_id == user_id
    )

    return db.session.scalar(statement)


def get_semester_by_id(semester_id):
    return db.session.get(Semester, semester_id)


def list_faculty():
    statement = select(Faculty).order_by(
        Faculty.first_name,
        Faculty.last_name,
    )

    return db.session.scalars(statement).all()


def get_faculty_slots(faculty_id, semester_id):
    statement = (
        select(TimetableSlot)
        .join(
            CourseOffering,
            TimetableSlot.offering_id == CourseOffering.id,
        )
        .options(
            selectinload(TimetableSlot.offering).selectinload(
                CourseOffering.course
            )
        )
        .where(
            TimetableSlot.faculty_id == faculty_id,
            TimetableSlot.status == "ACTIVE",
            CourseOffering.semester_id == semester_id,
        )
        .order_by(
            TimetableSlot.day_of_week,
            TimetableSlot.start_time,
        )
    )

    return db.session.scalars(statement).unique().all()


def get_workload_policy(faculty_id, semester_id):
    statement = select(FacultyWorkloadPolicy).where(
        FacultyWorkloadPolicy.faculty_id == faculty_id,
        FacultyWorkloadPolicy.semester_id == semester_id,
    )

    return db.session.scalar(statement)


def list_workload_policies(
    faculty_id=None,
    semester_id=None,
):
    statement = select(FacultyWorkloadPolicy).order_by(
        FacultyWorkloadPolicy.created_at.desc()
    )

    if faculty_id is not None:
        statement = statement.where(
            FacultyWorkloadPolicy.faculty_id == faculty_id
        )

    if semester_id is not None:
        statement = statement.where(
            FacultyWorkloadPolicy.semester_id == semester_id
        )

    return db.session.scalars(statement).all()


def get_policy_by_id(policy_id):
    return db.session.get(FacultyWorkloadPolicy, policy_id)