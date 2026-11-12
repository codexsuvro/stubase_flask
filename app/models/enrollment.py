
from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Enrollment(UUIDMixin, BaseModel):

    __tablename__ = "enrollments"

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "offering_id",
            name="uq_student_offering",
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

    offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id"),
        nullable=True,
        index=True,
    )

    offering = db.relationship(
        "CourseOffering",
        back_populates="enrollments",
        lazy="selectin",
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

    assessment_results = db.relationship(
        "AssessmentResult",
        back_populates="enrollment",
        lazy="selectin",
    )
    
    course_grade = db.relationship(
        "CourseGrade",
        back_populates="enrollment",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Enrollment {self.student_id} "
            f"{self.course_id}>"
        )