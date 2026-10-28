from sqlalchemy import select
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.models.department import Department


def get_role_by_name(role_name: str) -> Role | None:
    statement = select(Role).where(
        Role.role_name == role_name
    )
    return db.session.scalar(statement)


def get_department_by_id(department_id) -> Department | None:
    return db.session.get(Department, department_id)


def get_user_by_email(email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.session.scalar(statement)


def get_user_by_username(username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.session.scalar(statement)


def list_users() -> list[User]:
    statement = select(User).order_by(User.created_at.desc())
    return list(db.session.scalars(statement).all())


def get_user_by_uuid(user_id):
    return db.session.get(User, user_id)
