from datetime import date
from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Attendance(UUIDMixin, BaseModel):

    __tablename__ = "attendances"
    
    __table_args__ = (
        db.UniqueConstraint(
            "enrollment_id",
            "attendance_date",
            name="uq_attendance_enrollment_date",
        ),
    )

    enrollment_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("enrollments.id"),
        nullable=False,
    )

    attendance_date = db.Column(
        db.Date,
        default=date.today,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
    )

    remarks = db.Column(
        db.String(255),
        nullable=True,
    )
    
    enrollment = db.relationship(
        "Enrollment",
        back_populates="attendances",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<Attendance {self.enrollment_id} "
            f"{self.attendance_date}>"
        )