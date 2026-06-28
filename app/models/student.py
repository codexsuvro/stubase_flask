from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Student(UUIDMixin, BaseModel):

    __tablename__ = "students"

    student_id = db.Column(
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

    gender = db.Column(
        db.String(20),
        nullable=False,
    )

    date_of_birth = db.Column(
        db.Date,
        nullable=False,
    )

    phone = db.Column(
        db.String(15),
        nullable=False,
    )

    admission_date = db.Column(
        db.Date,
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
        back_populates="students",
        lazy="selectin"
    )
    
    user = db.relationship(
        "User",
        back_populates="student",
        lazy="selectin",
    )

    enrollments = db.relationship(
        "Enrollment",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return (
            f"<Student {self.student_id} "
            f"{self.admission_date}>"
        )