from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.faculty import Faculty
from app.models.student import Student
from app.users.repository import (
    get_role_by_name,
    get_department_by_id,
    get_user_by_email,
    get_user_by_username,
)
from app.utils.security import hash_password


class UserAlreadyExistsError(Exception):
    pass


class InvalidRoleError(Exception):
    pass


class DepartmentNotFoundError(Exception):
    pass


def create_user_account(data: dict) -> User:
    username = data["username"].strip()
    email = data["email"].strip().lower()
    role_name = data["role"].strip().upper()

    if not username:
        raise ValueError("Username cannot be blank.")

    if role_name not in {"FACULTY", "STUDENT"}:
        raise InvalidRoleError(
            "Only FACULTY and STUDENT accounts can be created here."
        )

    if get_user_by_email(email):
        raise UserAlreadyExistsError(
            "An account with this email already exists."
        )

    if get_user_by_username(username):
        raise UserAlreadyExistsError(
            "An account with this username already exists."
        )

    role = get_role_by_name(role_name)

    if role is None:
        raise InvalidRoleError(
            f"The {role_name} role has not been seeded in the database."
        )

    profile_data = data.get(
        "faculty_profile" if role_name == "FACULTY"
        else "student_profile"
    )

    department = get_department_by_id(profile_data["department_id"])

    if department is None:
        raise DepartmentNotFoundError(
            "The specified department does not exist."
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data["password"]),
        role_id=role.id,
        is_active=True,
        # Admin-created accounts are considered verified/approved.
        is_verified=True,
    )

    try:
        db.session.add(user)
        db.session.flush()  # Generate user.id without committing.

        if role_name == "FACULTY":
            faculty = Faculty(
                faculty_id=profile_data["faculty_id"].strip(),
                first_name=profile_data["first_name"].strip(),
                last_name=profile_data["last_name"].strip(),
                designation=profile_data["designation"].strip(),
                email=email,
                phone=profile_data["phone"].strip(),
                department_id=profile_data["department_id"],
                user_id=user.id,
            )
            db.session.add(faculty)

        else:
            student = Student(
                student_id=profile_data["student_id"].strip(),
                first_name=profile_data["first_name"].strip(),
                last_name=profile_data["last_name"].strip(),
                gender=profile_data["gender"].strip(),
                date_of_birth=profile_data["date_of_birth"],
                phone=profile_data["phone"].strip(),
                admission_date=profile_data["admission_date"],
                department_id=profile_data["department_id"],
                user_id=user.id,
            )
            db.session.add(student)

        db.session.commit()
        return user

    except IntegrityError as exc:
        db.session.rollback()
        raise UserAlreadyExistsError(
            "A username, email, faculty ID, or student ID already exists."
        ) from exc

    except Exception:
        db.session.rollback()
        raise
