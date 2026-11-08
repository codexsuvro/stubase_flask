from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class AssessmentResult(UUIDMixin, BaseModel):

    __tablename__ = "assessment_results"

    __table_args__ = (
        db.UniqueConstraint(
            "assessment_id",
            "enrollment_id",
            name="uq_assessment_result_enrollment",
        ),
        db.CheckConstraint(
            "marks_obtained >= 0",
            name="ck_result_marks_non_negative",
        ),
    )

    assessment_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("assessments.id"),
        nullable=False,
        index=True,
    )

    enrollment_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("enrollments.id"),
        nullable=False,
        index=True,
    )

    marks_obtained = db.Column(
        db.Numeric(7, 2),
        nullable=False,
    )

    remarks = db.Column(
        db.Text,
        nullable=True,
    )

    graded_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    assessment = db.relationship(
        "Assessment",
        back_populates="results",
        lazy="selectin",
    )

    enrollment = db.relationship(
        "Enrollment",
        back_populates="assessment_results",
        lazy="selectin",
    )

    grader = db.relationship(
        "User",
        back_populates="graded_assessment_results",
        foreign_keys=[graded_by],
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<AssessmentResult "
            f"{self.assessment_id} "
            f"{self.enrollment_id} "
            f"{self.marks_obtained}>"
        )