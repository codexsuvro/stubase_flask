from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Course(UUIDMixin, BaseModel):

    __tablename__ = "courses"

    course_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
    )

    course_name = db.Column(
        db.String(100),
        nullable=False,
    )

    credits = db.Column(
        db.Integer,
        nullable=False,
    )

    semester = db.Column(
        db.Integer,
        nullable=False,
    )

    department_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("departments.id"),
        nullable=False,
    )

    faculty_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("faculties.id"),
        nullable=False,
    )
    
    department = db.relationship(
        "Department",
        back_populates="courses",
        lazy="selectin",
    )

    faculty = db.relationship(
        "Faculty",
        back_populates="courses",
        lazy="selectin",
    )

    enrollments = db.relationship(
        "Enrollment",
        back_populates="course",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return (
            f"<Course {self.course_code} "
            f"{self.course_name}>"
        )