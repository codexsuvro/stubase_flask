from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Assignment(UUIDMixin, BaseModel):
    __tablename__ = "assignments"

    __table_args__ = (
        db.CheckConstraint(
            "max_marks > 0",
            name="ck_assignment_max_marks",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'CLOSED')",
            name="ck_assignment_status",
        ),
        db.CheckConstraint(
            "due_at > available_from",
            name="ck_assignment_due_after_available",
        ),
    )

    offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.Text, nullable=True)

    max_marks = db.Column(db.Numeric(8, 2), nullable=False)

    available_from = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    due_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    allow_late_submissions = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    allow_resubmissions = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    offering = db.relationship(
        "CourseOffering",
        lazy="selectin",
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    submissions = db.relationship(
        "AssignmentSubmission",
        back_populates="assignment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Assignment {self.title} "
            f"offering={self.offering_id}>"
        )


class AssignmentSubmission(UUIDMixin, BaseModel):
    __tablename__ = "assignment_submissions"

    __table_args__ = (
        db.UniqueConstraint(
            "assignment_id",
            "student_id",
            name="uq_assignment_submission_student",
        ),
        db.CheckConstraint(
            "resubmission_count >= 0",
            name="ck_assignment_resubmission_count",
        ),
        db.CheckConstraint(
            "marks_obtained IS NULL OR marks_obtained >= 0",
            name="ck_assignment_marks_non_negative",
        ),
        db.CheckConstraint(
            "status IN ('SUBMITTED', 'GRADED')",
            name="ck_assignment_submission_status",
        ),
    )

    assignment_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    text_response = db.Column(
        db.Text,
        nullable=True,
    )

    submitted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    is_late = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    resubmission_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="SUBMITTED",
        server_default="SUBMITTED",
    )

    marks_obtained = db.Column(
        db.Numeric(8, 2),
        nullable=True,
    )

    feedback = db.Column(
        db.Text,
        nullable=True,
    )

    graded_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    graded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    assignment = db.relationship(
        "Assignment",
        back_populates="submissions",
        lazy="selectin",
    )

    student = db.relationship(
        "Student",
        lazy="selectin",
    )

    grader = db.relationship(
        "User",
        foreign_keys=[graded_by],
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<AssignmentSubmission "
            f"assignment={self.assignment_id} "
            f"student={self.student_id} "
            f"status={self.status}>"
        )
