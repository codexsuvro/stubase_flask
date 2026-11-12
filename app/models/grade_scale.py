from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class GradeScale(UUIDMixin, BaseModel):

    __tablename__ = "grade_scales"

    __table_args__ = (
        db.UniqueConstraint(
            "grading_scheme_id",
            "letter_grade",
            name="uq_scheme_letter_grade",
        ),
        db.CheckConstraint(
            "min_percentage >= 0 AND max_percentage <= 100",
            name="ck_grade_percentage_range",
        ),
        db.CheckConstraint(
            "min_percentage <= max_percentage",
            name="ck_grade_percentage_order",
        ),
        db.CheckConstraint(
            "grade_point >= 0",
            name="ck_grade_point_non_negative",
        ),
        db.CheckConstraint(
            "is_passing IN (TRUE, FALSE)",
            name="ck_grade_scale_passing",
        ),
    )

    grading_scheme_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("grading_schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    letter_grade = db.Column(
        db.String(5),
        nullable=False,
    )

    min_percentage = db.Column(
        db.Numeric(5, 2),
        nullable=False,
    )

    max_percentage = db.Column(
        db.Numeric(5, 2),
        nullable=False,
    )

    grade_point = db.Column(
        db.Numeric(4, 2),
        nullable=False,
    )

    is_passing = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.true(),
    )

    grading_scheme = db.relationship(
        "GradingScheme",
        back_populates="grade_scales",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<GradeScale {self.letter_grade} "
            f"{self.min_percentage}-{self.max_percentage}>"
        )