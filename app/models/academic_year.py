from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class AcademicYear(UUIDMixin, BaseModel):

    __tablename__ = "academic_years"

    __table_args__ = (
        db.CheckConstraint(
            "start_date < end_date",
            name="ck_academic_year_dates",
        ),
        db.CheckConstraint(
            "status IN ('PLANNED', 'ACTIVE', 'COMPLETED')",
            name="ck_academic_year_status",
        ),
    )

    name = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        index=True,
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

    semesters = db.relationship(
        "Semester",
        back_populates="academic_year",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<AcademicYear {self.name}>"