from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Semester(UUIDMixin, BaseModel):

    __tablename__ = "semesters"

    __table_args__ = (
        db.UniqueConstraint(
            "academic_year_id",
            "semester_number",
            name="uq_academic_year_semester_number",
        ),
        db.CheckConstraint(
            "semester_number BETWEEN 1 AND 8",
            name="ck_semester_number",
        ),
        db.CheckConstraint(
            "start_date < end_date",
            name="ck_semester_dates",
        ),
        db.CheckConstraint(
            "status IN ('PLANNED', 'ACTIVE', 'COMPLETED')",
            name="ck_semester_status",
        ),
    )

    academic_year_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    semester_number = db.Column(
        db.Integer,
        nullable=False,
    )

    semester_name = db.Column(
        db.String(50),
        nullable=False,
    )

    start_date = db.Column(
        db.Date,
        nullable=False,
    )

    end_date = db.Column(
        db.Date,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PLANNED",
        server_default="PLANNED",
    )

    academic_year = db.relationship(
        "AcademicYear",
        back_populates="semesters",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<Semester {self.semester_number} "
            f"{self.semester_name}>"
        )