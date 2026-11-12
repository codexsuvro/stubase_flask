from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class CourseGrade(UUIDMixin, BaseModel):

    __tablename__ = "course_grades"

    __table_args__ = (
        db.UniqueConstraint(
            "enrollment_id",
            name="uq_course_grade_enrollment",
        ),
        db.CheckConstraint(
            "total_marks >= 0",
            name="ck_course_grade_marks_non_negative",
        ),
        db.CheckConstraint(
            "percentage >= 0 AND percentage <= 100",
            name="ck_course_grade_percentage",
        ),
        db.CheckConstraint(
            "grade_point >= 0",
            name="ck_course_grade_point",
        ),
        db.CheckConstraint(
            "result_status IN ('PASS', 'FAIL', 'INCOMPLETE')",
            name="ck_course_grade_result_status",
        ),
        db.CheckConstraint(
            "publication_status IN ('DRAFT', 'PUBLISHED')",
            name="ck_course_grade_publication_status",
        ),
    )

    enrollment_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grading_scheme_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("grading_schemes.id"),
        nullable=False,
        index=True,
    )

    total_marks = db.Column(
        db.Numeric(8, 2),
        nullable=False,
    )

    percentage = db.Column(
        db.Numeric(5, 2),
        nullable=False,
    )

    letter_grade = db.Column(
        db.String(5),
        nullable=True,
    )

    grade_point = db.Column(
        db.Numeric(4, 2),
        nullable=False,
    )

    result_status = db.Column(
        db.String(20),
        nullable=False,
        default="INCOMPLETE",
        server_default="INCOMPLETE",
    )

    publication_status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    published_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    published_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    enrollment = db.relationship(
        "Enrollment",
        back_populates="course_grade",
        lazy="selectin",
    )

    grading_scheme = db.relationship(
        "GradingScheme",
        back_populates="course_grades",
        lazy="selectin",
    )

    publisher = db.relationship(
        "User",
        foreign_keys=[published_by],
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<CourseGrade {self.enrollment_id} "
            f"{self.letter_grade}>"
        )