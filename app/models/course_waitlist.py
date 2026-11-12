from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class CourseWaitlist(UUIDMixin, BaseModel):

    __tablename__ = "course_waitlists"

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "offering_id",
            name="uq_waitlist_student_offering",
        ),
        db.CheckConstraint(
            "status IN ('WAITING', 'PROMOTED', 'CANCELLED', 'INELIGIBLE')",
            name="ck_waitlist_status",
        ),
    )

    student_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="WAITING",
        server_default="WAITING",
        index=True,
    )

    promoted_enrollment_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("enrollments.id"),
        nullable=True,
    )

    student = db.relationship(
        "Student",
        lazy="selectin",
    )

    offering = db.relationship(
        "CourseOffering",
        lazy="selectin",
    )

    promoted_enrollment = db.relationship(
        "Enrollment",
        foreign_keys=[promoted_enrollment_id],
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<CourseWaitlist "
            f"{self.student_id} "
            f"{self.offering_id} "
            f"{self.status}>"
        )