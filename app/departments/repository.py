from sqlalchemy import select
from app.extensions import db
from app.models.department import Department


def get_department_by_code(code: str) -> Department | None:
    statement = select(Department).where(
        Department.department_code == code
    )
    return db.session.scalar(statement)


def get_department_by_email(email: str) -> Department | None:
    statement = select(Department).where(
        Department.email == email
    )
    return db.session.scalar(statement)


def get_department_by_id(department_id) -> Department | None:
    return db.session.get(Department, department_id)


def list_departments() -> list[Department]:
    statement = select(Department).order_by(
        Department.department_code.asc()
    )
    return list(db.session.scalars(statement).all())