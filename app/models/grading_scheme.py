from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class GradingScheme(UUIDMixin, BaseModel):

    __tablename__ = "grading_schemes"

    __table_args__ = (
        db.UniqueConstraint(
            "scheme_name",
            name="uq_grading_scheme_name",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_grading_scheme_status",
        ),
    )

    scheme_name = db.Column(
        db.String(100),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )

    grade_scales = db.relationship(
        "GradeScale",
        back_populates="grading_scheme",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="GradeScale.min_percentage.desc()",
    )

    course_grades = db.relationship(
        "CourseGrade",
        back_populates="grading_scheme",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<GradingScheme {self.scheme_name}>"