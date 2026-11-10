
from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Assessment(UUIDMixin, BaseModel):

    __tablename__ = "assessments"

    __table_args__ = (
        db.UniqueConstraint(
            "offering_id",
            "assessment_type",
            "sequence_number",
            name="uq_offering_assessment_sequence",
        ),
    )

    assessment_name = db.Column(
        db.String(100),
        nullable=False,
    )

    assessment_type = db.Column(
        db.String(20),
        nullable=False,
    )

    sequence_number = db.Column(
        db.Integer,
        nullable=False,
        default=1,
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

    max_marks = db.Column(
        db.Numeric(7, 2),
        nullable=False,
    )

    passing_marks = db.Column(
        db.Numeric(7, 2),
        nullable=False,
    )

    assessment_date = db.Column(
        db.Date,
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id"),
        nullable=True,
        index=True,
    )

    offering = db.relationship(
        "CourseOffering",
        back_populates="assessments",
        lazy="selectin",
    )

    course = db.relationship(
        "Course",
        back_populates="assessments",
        lazy="selectin",
    )

    results = db.relationship(
        "AssessmentResult",
        back_populates="assessment",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<Assessment {self.assessment_name} "
            f"{self.assessment_type}>"
        )