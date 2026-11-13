from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class FacultyWorkloadPolicy(UUIDMixin, BaseModel):
    __tablename__ = "faculty_workload_policies"

    __table_args__ = (
        db.UniqueConstraint(
            "faculty_id",
            "semester_id",
            name="uq_faculty_workload_policy_semester",
        ),
        db.CheckConstraint(
            "minimum_hours >= 0",
            name="ck_workload_minimum_hours",
        ),
        db.CheckConstraint(
            "maximum_hours > 0",
            name="ck_workload_maximum_hours",
        ),
        db.CheckConstraint(
            "minimum_hours <= maximum_hours",
            name="ck_workload_hours_range",
        ),
    )

    faculty_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("faculties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    minimum_hours = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0,
        server_default="0",
    )

    maximum_hours = db.Column(
        db.Numeric(5, 2),
        nullable=False,
    )

    remarks = db.Column(
        db.String(500),
        nullable=True,
    )

    faculty = db.relationship(
        "Faculty",
        lazy="selectin",
    )

    semester = db.relationship(
        "Semester",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<FacultyWorkloadPolicy "
            f"faculty={self.faculty_id} "
            f"semester={self.semester_id}>"
        )