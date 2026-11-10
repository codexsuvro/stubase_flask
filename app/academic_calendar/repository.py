from sqlalchemy import select
from app.extensions import db
from app.models.academic_year import AcademicYear
from app.models.semester import Semester


def get_academic_year_by_id(academic_year_id):
    return db.session.get(AcademicYear, academic_year_id)


def get_academic_year_by_name(name):
    statement = select(AcademicYear).where(
        AcademicYear.name == name
    )
    return db.session.scalar(statement)


def list_academic_years():
    statement = select(AcademicYear).order_by(
        AcademicYear.start_date.desc()
    )
    return list(db.session.scalars(statement).all())


def get_semester_by_id(semester_id):
    return db.session.get(Semester, semester_id)


def get_semester_by_number(academic_year_id, semester_number):
    statement = select(Semester).where(
        Semester.academic_year_id == academic_year_id,
        Semester.semester_number == semester_number,
    )
    return db.session.scalar(statement)


def list_semesters(academic_year_id=None, status=None):
    statement = select(Semester)

    if academic_year_id is not None:
        statement = statement.where(
            Semester.academic_year_id == academic_year_id
        )

    if status is not None:
        statement = statement.where(
            Semester.status == status
        )

    statement = statement.order_by(
        Semester.semester_number.asc()
    )

    return list(db.session.scalars(statement).all())