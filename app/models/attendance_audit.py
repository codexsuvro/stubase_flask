from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class AttendanceAudit(UUIDMixin, BaseModel):

    __tablename__ = "attendance_audits"

    attendance_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("attendances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    changed_by_user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    previous_status = db.Column(
        db.String(20),
        nullable=False,
    )

    new_status = db.Column(
        db.String(20),
        nullable=False,
    )

    previous_remarks = db.Column(
        db.String(255),
        nullable=True,
    )

    new_remarks = db.Column(
        db.String(255),
        nullable=True,
    )

    attendance = db.relationship(
        "Attendance",
        lazy="selectin",
    )

    changed_by = db.relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<AttendanceAudit {self.attendance_id} "
            f"{self.previous_status}->{self.new_status}>"
        )