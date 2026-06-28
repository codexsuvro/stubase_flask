from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Faculty(UUIDMixin, BaseModel):

    __tablename__ = "faculties"

    faculty_id = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
    )

    first_name = db.Column(
        db.String(50),
        nullable=False,
    )

    last_name = db.Column(
        db.String(50),
        nullable=False,
    )

    designation = db.Column(
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

    department_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("departments.id"),
        nullable=False,
    )

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    
    department = db.relationship(
        "Department",
        back_populates="faculties",
        lazy="selectin",
    )

    user = db.relationship(
        "User",
        back_populates="faculty",
        lazy="selectin",
    )

    courses = db.relationship(
        "Course",
        back_populates="faculty",
        lazy="selectin",
    )
    
    def __repr__(self):
        return (
            f"<Faculty {self.faculty_id} "
            f"{self.phone}>"
        )