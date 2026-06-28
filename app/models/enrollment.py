from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Enrollment(UUIDMixin, BaseModel):

    __tablename__ = "enrollments"
    
    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "course_id",
            "academic_year",
            "semester",
            name="uq_student_course_semester",
        ),
    )

    student_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("students.id"),
        nullable=False,
    )

    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id"),
        nullable=False,
    )

    semester = db.Column(
        db.Integer,
        nullable=False,
    )

    academic_year = db.Column(
        db.String(20),
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
    )
    
    student = db.relationship(
        "Student",
        back_populates="enrollments",
        lazy="selectin",
    )

    course = db.relationship(
        "Course",
        back_populates="enrollments",
        lazy="selectin",
    )

    attendances = db.relationship(
        "Attendance",
        back_populates="enrollment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Enrollment {self.student_id} "
            f"{self.course_id}>"
        )