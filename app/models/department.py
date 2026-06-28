from app.extensions import db
from app.models.base import BaseModel, UUIDMixin

class Department(UUIDMixin, BaseModel):
    __tablename__ = "departments"

    department_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
    )

    department_name = db.Column(
        db.String(100),
        nullable=False,
    )

    hod_name = db.Column(
        db.String(100),
        nullable=False,
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
    )

    phone = db.Column(
        db.String(20),
        nullable=False,
    )
    
    students = db.relationship(
        "Student",
        back_populates="department",
        lazy="selectin"
    )
    
    faculties = db.relationship(
        "Faculty",
        back_populates="department",
        lazy="selectin",
    )

    courses = db.relationship(
        "Course",
        back_populates="department",
        lazy="selectin",
    )
    
    def __repr__(self):
        return (
            f"<Department {self.department_code} "
            f"{self.department_name}>"
        )