
from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class CourseOffering(UUIDMixin, BaseModel):

    __tablename__ = "course_offerings"

    __table_args__ = (
        db.UniqueConstraint(
            "course_id",
            "semester_id",
            "section_code",
            name="uq_course_offering_course_semester_section",
        ),
        db.CheckConstraint(
            "capacity > 0",
            name="ck_course_offering_capacity",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'OPEN', 'CLOSED', 'CANCELLED')",
            name="ck_course_offering_status",
        ),
    )

    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )

    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id"),
        nullable=False,
        index=True,
    )

    faculty_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("faculties.id"),
        nullable=False,
        index=True,
    )

    section_code = db.Column(
        db.String(10),
        nullable=False,
    )

    capacity = db.Column(
        db.Integer,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    course = db.relationship(
        "Course",
        back_populates="offerings",
        lazy="selectin",
    )

    semester = db.relationship(
        "Semester",
        back_populates="course_offerings",
        lazy="selectin",
    )

    faculty = db.relationship(
        "Faculty",
        back_populates="course_offerings",
        lazy="selectin",
    )

    enrollments = db.relationship(
        "Enrollment",
        back_populates="offering",
        lazy="selectin",
    )

    assessments = db.relationship(
        "Assessment",
        back_populates="offering",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<CourseOffering {self.course_id} "
            f"{self.section_code}>"
        )
