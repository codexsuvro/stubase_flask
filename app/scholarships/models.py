from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class ScholarshipProgram(UUIDMixin, BaseModel):
    __tablename__ = "scholarship_programs"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('DRAFT', 'OPEN', 'CLOSED', 'ARCHIVED')",
            name="ck_scholarship_program_status",
        ),
        db.CheckConstraint(
            "award_type IN ('FIXED', 'PERCENTAGE')",
            name="ck_scholarship_program_award_type",
        ),
        db.CheckConstraint(
            "award_value > 0",
            name="ck_scholarship_program_award_value",
        ),
        db.CheckConstraint(
            "award_type != 'PERCENTAGE' OR award_value <= 100",
            name="ck_scholarship_program_percentage",
        ),
        db.CheckConstraint(
            "max_award_amount IS NULL OR max_award_amount > 0",
            name="ck_scholarship_program_max_award",
        ),
        db.CheckConstraint(
            "award_type = 'PERCENTAGE' OR max_award_amount IS NULL",
            name="ck_scholarship_program_max_award_type",
        ),
        db.CheckConstraint(
            "total_budget_amount IS NULL OR total_budget_amount > 0",
            name="ck_scholarship_program_budget",
        ),
        db.CheckConstraint(
            "max_recipients IS NULL OR max_recipients > 0",
            name="ck_scholarship_program_max_recipients",
        ),
        db.CheckConstraint(
            "total_budget_amount IS NULL OR award_type != 'PERCENTAGE' "
            "OR max_award_amount IS NOT NULL",
            name="ck_scholarship_program_budget_cap",
        ),
        db.CheckConstraint(
            "min_cgpa IS NULL OR min_cgpa >= 0",
            name="ck_scholarship_program_min_cgpa",
        ),
        db.CheckConstraint(
            "application_open_at < application_close_at",
            name="ck_scholarship_program_application_dates",
        ),
        db.CheckConstraint(
            "length(trim(code)) > 0",
            name="ck_scholarship_program_code_nonblank",
        ),
        db.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_scholarship_program_name_nonblank",
        ),
        db.CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_scholarship_program_currency_code",
        ),
        db.UniqueConstraint("code", name="uq_scholarship_program_code"),
        db.Index(
            "ix_scholarship_program_academic_scope",
            "academic_year_id",
            "semester_id",
            "department_id",
            "status",
        ),
    )

    code = db.Column(db.String(40), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    academic_year_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    department_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    application_open_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    application_close_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    min_cgpa = db.Column(db.Numeric(5, 2), nullable=True)
    award_type = db.Column(db.String(20), nullable=False)
    award_value = db.Column(db.Numeric(12, 2), nullable=False)
    max_award_amount = db.Column(db.Numeric(12, 2), nullable=True)
    total_budget_amount = db.Column(db.Numeric(12, 2), nullable=True)
    max_recipients = db.Column(db.Integer, nullable=True)
    currency_code = db.Column(
        db.String(3),
        nullable=False,
        default="INR",
        server_default="INR",
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )
    opened_at = db.Column(db.DateTime(timezone=True), nullable=True)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)

    academic_year = db.relationship("AcademicYear", lazy="selectin")
    semester = db.relationship("Semester", lazy="selectin")
    department = db.relationship("Department", lazy="selectin")
    applications = db.relationship(
        "ScholarshipApplication",
        back_populates="program",
        lazy="selectin",
    )


class ScholarshipApplication(UUIDMixin, BaseModel):
    __tablename__ = "scholarship_applications"

    __table_args__ = (
        db.UniqueConstraint(
            "program_id",
            "student_id",
            name="uq_scholarship_application_student",
        ),
        db.CheckConstraint(
            "status IN ('SUBMITTED', 'APPROVED', 'REJECTED', 'WITHDRAWN')",
            name="ck_scholarship_application_status",
        ),
        db.CheckConstraint(
            "(status IN ('APPROVED', 'REJECTED') AND decided_at IS NOT NULL "
            "AND decided_by IS NOT NULL) OR "
            "(status IN ('SUBMITTED', 'WITHDRAWN') AND decided_at IS NULL "
            "AND decided_by IS NULL)",
            name="ck_scholarship_application_decision",
        ),
        db.Index(
            "ix_scholarship_application_program_status",
            "program_id",
            "status",
        ),
    )

    program_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("scholarship_programs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    statement = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="SUBMITTED",
        server_default="SUBMITTED",
    )
    submitted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    decided_at = db.Column(db.DateTime(timezone=True), nullable=True)
    decided_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    decision_notes = db.Column(db.String(1000), nullable=True)

    program = db.relationship(
        "ScholarshipProgram",
        back_populates="applications",
        lazy="selectin",
    )
    student = db.relationship("Student", lazy="selectin")
    decision_maker = db.relationship(
        "User",
        foreign_keys=[decided_by],
        lazy="selectin",
    )
    award = db.relationship(
        "ScholarshipAward",
        back_populates="application",
        uselist=False,
        lazy="selectin",
    )
    documents = db.relationship(
        "ScholarshipApplicationDocument",
        back_populates="application",
        lazy="selectin",
        order_by="ScholarshipApplicationDocument.uploaded_at",
    )


class ScholarshipApplicationDocument(UUIDMixin, BaseModel):
    __tablename__ = "scholarship_application_documents"

    __table_args__ = (
        db.Index(
            "ix_scholarship_application_document_application",
            "application_id",
            "uploaded_at",
        ),
    )

    application_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("scholarship_applications.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    object_key = db.Column(
        db.String(500),
        nullable=False,
        unique=True,
    )
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    uploaded_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    application = db.relationship(
        "ScholarshipApplication",
        back_populates="documents",
        lazy="selectin",
    )
    uploader = db.relationship(
        "User",
        foreign_keys=[uploaded_by],
        lazy="selectin",
    )


class ScholarshipAward(UUIDMixin, BaseModel):
    __tablename__ = "scholarship_awards"

    __table_args__ = (
        db.CheckConstraint(
            "award_type IN ('FIXED', 'PERCENTAGE')",
            name="ck_scholarship_award_type",
        ),
        db.CheckConstraint(
            "award_value > 0",
            name="ck_scholarship_award_value",
        ),
        db.CheckConstraint(
            "award_type != 'PERCENTAGE' OR award_value <= 100",
            name="ck_scholarship_award_percentage",
        ),
        db.CheckConstraint(
            "max_award_amount IS NULL OR max_award_amount > 0",
            name="ck_scholarship_award_max_amount",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'REVOKED')",
            name="ck_scholarship_award_status",
        ),
        db.CheckConstraint(
            "(status = 'REVOKED' AND revoked_at IS NOT NULL "
            "AND revoked_by IS NOT NULL AND revoked_reason IS NOT NULL "
            "AND length(trim(revoked_reason)) > 0) OR "
            "(status = 'ACTIVE' AND revoked_at IS NULL "
            "AND revoked_by IS NULL AND revoked_reason IS NULL)",
            name="ck_scholarship_award_revocation",
        ),
        db.UniqueConstraint(
            "application_id",
            name="uq_scholarship_award_application",
        ),
        db.Index(
            "ix_scholarship_award_student_period",
            "student_id",
            "academic_year_id",
            "semester_id",
            "status",
        ),
    )

    application_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("scholarship_applications.id", ondelete="RESTRICT"),
        nullable=False,
    )
    program_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("scholarship_programs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    student_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    academic_year_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    department_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=True,
    )
    award_type = db.Column(db.String(20), nullable=False)
    award_value = db.Column(db.Numeric(12, 2), nullable=False)
    max_award_amount = db.Column(db.Numeric(12, 2), nullable=True)
    currency_code = db.Column(db.String(3), nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )
    awarded_at = db.Column(db.DateTime(timezone=True), nullable=False)
    awarded_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    award_reason = db.Column(db.String(1000), nullable=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    revoked_reason = db.Column(db.String(500), nullable=True)

    application = db.relationship(
        "ScholarshipApplication",
        back_populates="award",
        lazy="selectin",
    )
    program = db.relationship("ScholarshipProgram", lazy="selectin")
    student = db.relationship("Student", lazy="selectin")
    awarding_user = db.relationship(
        "User",
        foreign_keys=[awarded_by],
        lazy="selectin",
    )
