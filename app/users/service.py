from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.role import Role
from app.users.repository import (
    get_role_by_name,
    get_department_by_id,
    get_user_by_email,
    get_user_by_username,
    get_user_by_uuid,
)
from app.utils.security import hash_password


class UserAlreadyExistsError(Exception):
    pass


class InvalidRoleError(Exception):
    pass


class DepartmentNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class LastActiveAdminError(Exception):
    pass


def create_user_account(data: dict) -> User:
    username = data["username"].strip()
    email = data["email"].strip().lower()
    role_name = data["role"].strip().upper()

    if not username:
        raise ValueError("Username cannot be blank.")

    if role_name not in {"FACULTY", "STUDENT"}:
        raise InvalidRoleError(
            "Only FACULTY and STUDENT accounts can be created through this endpoint."
        )

    if get_user_by_email(email):
        raise UserAlreadyExistsError("Email address is already registered.")

    if get_user_by_username(username):
        raise UserAlreadyExistsError("Username is already registered.")

    role = get_role_by_name(role_name)

    if role is None:
        raise InvalidRoleError("The specified role does not exist.")

    profile_data = data.get(
        "faculty_profile" if role_name == "FACULTY" else "student_profile"
    )

    department = get_department_by_id(profile_data["department_id"])

    if department is None:
        raise DepartmentNotFoundError("Department not found.")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data["password"]),
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )

    try:
        db.session.add(user)
        db.session.flush()

        if role_name == "FACULTY":
            faculty = Faculty(
                faculty_id=profile_data["faculty_id"],
                first_name=profile_data["first_name"],
                last_name=profile_data["last_name"],
                designation=profile_data["designation"],
                phone=profile_data["phone"],
                department_id=profile_data["department_id"],
                user_id=user.id,
            )
            db.session.add(faculty)

        else:
            student = Student(
                student_id=profile_data["student_id"],
                first_name=profile_data["first_name"],
                last_name=profile_data["last_name"],
                gender=profile_data["gender"],
                date_of_birth=profile_data["date_of_birth"],
                phone=profile_data["phone"],
                admission_date=profile_data["admission_date"],
                department_id=profile_data["department_id"],
                user_id=user.id,
            )
            db.session.add(student)

        db.session.commit()
        return user

    except IntegrityError:
        db.session.rollback()
        raise UserAlreadyExistsError(
            "A user or profile with the supplied unique details already exists."
        )

    except Exception:
        db.session.rollback()
        raise


def ensure_another_active_admin_exists(user: User) -> None:
    """
    Prevent disabling or unverifying the last active, verified administrator.
    """

    statement = (
        select(func.count(User.id))
        .join(Role, User.role_id == Role.id)
        .where(
            Role.role_name == "ADMIN",
            User.id != user.id,
            User.is_active.is_(True),
            User.is_verified.is_(True),
        )
    )

    other_active_admins = db.session.scalar(statement) or 0

    if other_active_admins == 0:
        raise LastActiveAdminError(
            "This operation is not allowed because at least one "
            "active and verified administrator must remain in the system."
        )


def update_user_status(user_id, is_active: bool) -> User:
    user = get_user_by_uuid(user_id)

    if user is None:
        raise UserNotFoundError("User account not found.")

    if user.is_active == is_active:
        return user

    if user.role and user.role.role_name == "ADMIN" and not is_active:
        ensure_another_active_admin_exists(user)

    try:
        user.is_active = is_active

        # Permanently invalidate all previously issued JWTs.
        user.token_version += 1

        db.session.commit()
        return user

    except Exception:
        db.session.rollback()
        raise


def update_user_verification(user_id, is_verified: bool) -> User:
    user = get_user_by_uuid(user_id)

    if user is None:
        raise UserNotFoundError("User account not found.")

    if user.is_verified == is_verified:
        return user

    if user.role and user.role.role_name == "ADMIN" and not is_verified:
        ensure_another_active_admin_exists(user)

    try:
        user.is_verified = is_verified

        # Permanently invalidate all previously issued JWTs.
        user.token_version += 1

        db.session.commit()
        return user

    except Exception:
        db.session.rollback()
        raise