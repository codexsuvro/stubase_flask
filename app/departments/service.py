from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.faculty import Faculty
from app.extensions import db
from app.models.department import Department
from app.departments.repository import (
    get_department_by_code,
    get_department_by_email,
)


class DepartmentAlreadyExistsError(Exception):
    pass


def create_department(data: dict) -> Department:
    department_code = data["department_code"].strip().upper()
    department_name = data["department_name"].strip()
    email = data["email"].strip().lower()
    phone = data["phone"].strip()

    if not all([department_code, department_name, email, phone]):
        raise ValueError("Department fields cannot be blank.")

    if get_department_by_code(department_code):
        raise DepartmentAlreadyExistsError(
            "A department with this code already exists."
        )

    if get_department_by_email(email):
        raise DepartmentAlreadyExistsError(
            "A department with this email already exists."
        )

    department = Department(
        department_code=department_code,
        department_name=department_name,
        email=email,
        phone=phone,
    )

    try:
        db.session.add(department)
        db.session.commit()
        return department

    except IntegrityError as exc:
        db.session.rollback()
        raise DepartmentAlreadyExistsError(
            "The department code or email is already in use."
        ) from exc

    except Exception:
        db.session.rollback()
        raise


class DepartmentNotFoundError(Exception):
    pass


class FacultyNotFoundError(Exception):
    pass


class InvalidDepartmentHODError(Exception):
    pass


def assign_department_hod(department_id, faculty_user_id):
    department = db.session.get(Department, department_id)

    if department is None:
        raise DepartmentNotFoundError("Department not found.")

    statement = select(Faculty).where(
        Faculty.user_id == faculty_user_id
    )
    faculty = db.session.scalar(statement)

    if faculty is None:
        raise FacultyNotFoundError(
            "No Faculty profile exists for this User account."
        )

    if faculty.department_id != department.id:
        raise InvalidDepartmentHODError(
            "The Faculty must belong to the department they are assigned to lead."
        )

    if (
        faculty.headed_department is not None
        and faculty.headed_department.id != department.id
    ):
        raise InvalidDepartmentHODError(
            "This Faculty is already the HOD of another department."
        )

    try:
        # Update the FK directly instead of assigning ORM relationships.
        department.hod_faculty_id = faculty.id

        db.session.commit()

        # Reload the HOD relationship from the database.
        db.session.refresh(department)

        return department

    except Exception:
        db.session.rollback()
        raise
