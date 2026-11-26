from decimal import Decimal

from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


FEE_STRUCTURE_STATUSES = ("DRAFT", "ACTIVE", "ARCHIVED")


class FeeStructure(UUIDMixin, BaseModel):
    __tablename__ = "fee_structures"

    __table_args__ = (
        db.CheckConstraint(
            "version > 0",
            name="ck_fee_structure_version",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')",
            name="ck_fee_structure_status",
        ),
        db.CheckConstraint(
            "length(trim(fee_code)) > 0",
            name="ck_fee_structure_code_nonblank",
        ),
        db.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_fee_structure_name_nonblank",
        ),
        db.CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_fee_structure_currency_code",
        ),
        db.CheckConstraint(
            "status != 'ACTIVE' OR activated_at IS NOT NULL",
            name="ck_fee_structure_active_timestamp",
        ),
        db.CheckConstraint(
            "(status = 'ARCHIVED' AND archived_at IS NOT NULL) OR "
            "(status != 'ARCHIVED' AND archived_at IS NULL)",
            name="ck_fee_structure_archived_timestamp",
        ),
        db.Index(
            "uq_fee_structure_department_version",
            "department_id",
            "academic_year_id",
            "semester_id",
            "fee_code",
            "version",
            unique=True,
            postgresql_where=db.text("course_offering_id IS NULL"),
            sqlite_where=db.text("course_offering_id IS NULL"),
        ),
        db.Index(
            "uq_fee_structure_offering_version",
            "department_id",
            "academic_year_id",
            "semester_id",
            "course_offering_id",
            "fee_code",
            "version",
            unique=True,
            postgresql_where=db.text("course_offering_id IS NOT NULL"),
            sqlite_where=db.text("course_offering_id IS NOT NULL"),
        ),
        db.Index(
            "ix_fee_structure_scope_status",
            "academic_year_id",
            "semester_id",
            "department_id",
            "status",
        ),
        db.Index(
            "uq_fee_structure_active_department_scope",
            "department_id",
            "academic_year_id",
            "semester_id",
            "fee_code",
            unique=True,
            postgresql_where=db.text(
                "course_offering_id IS NULL AND status = 'ACTIVE'"
            ),
            sqlite_where=db.text(
                "course_offering_id IS NULL AND status = 'ACTIVE'"
            ),
        ),
        db.Index(
            "uq_fee_structure_active_offering_scope",
            "department_id",
            "academic_year_id",
            "semester_id",
            "course_offering_id",
            "fee_code",
            unique=True,
            postgresql_where=db.text(
                "course_offering_id IS NOT NULL AND status = 'ACTIVE'"
            ),
            sqlite_where=db.text(
                "course_offering_id IS NOT NULL AND status = 'ACTIVE'"
            ),
        ),
    )

    department_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    academic_year_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    course_offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    fee_code = db.Column(
        db.String(40),
        nullable=False,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    version = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

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

    activated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    archived_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    department = db.relationship("Department", lazy="selectin")
    academic_year = db.relationship("AcademicYear", lazy="selectin")
    semester = db.relationship("Semester", lazy="selectin")
    course_offering = db.relationship("CourseOffering", lazy="selectin")

    items = db.relationship(
        "FeeStructureItem",
        back_populates="fee_structure",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="FeeStructureItem.sequence_order",
    )


class FeeStructureItem(UUIDMixin, BaseModel):
    __tablename__ = "fee_structure_items"

    __table_args__ = (
        db.UniqueConstraint(
            "fee_structure_id",
            "item_code",
            name="uq_fee_structure_item_code",
        ),
        db.UniqueConstraint(
            "fee_structure_id",
            "sequence_order",
            name="uq_fee_structure_item_sequence",
        ),
        db.CheckConstraint(
            "amount > 0",
            name="ck_fee_structure_item_amount",
        ),
        db.CheckConstraint(
            "sequence_order > 0",
            name="ck_fee_structure_item_sequence",
        ),
        db.CheckConstraint(
            "length(trim(item_code)) > 0",
            name="ck_fee_structure_item_code_nonblank",
        ),
        db.CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_fee_structure_item_name_nonblank",
        ),
    )

    fee_structure_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("fee_structures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_code = db.Column(
        db.String(40),
        nullable=False,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    is_mandatory = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.true(),
    )

    sequence_order = db.Column(
        db.Integer,
        nullable=False,
    )

    fee_structure = db.relationship(
        "FeeStructure",
        back_populates="items",
        lazy="selectin",
    )


class StudentFeeCharge(UUIDMixin, BaseModel):
    __tablename__ = "student_fee_charges"

    __table_args__ = (
        db.CheckConstraint(
            "amount > 0",
            name="ck_student_fee_charge_amount",
        ),
        db.CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_student_fee_charge_currency_code",
        ),
        db.CheckConstraint(
            "status IN ('OPEN', 'VOID')",
            name="ck_student_fee_charge_status",
        ),
        db.CheckConstraint(
            "(status = 'VOID' AND voided_at IS NOT NULL AND "
            "voided_by IS NOT NULL AND void_reason IS NOT NULL AND "
            "length(trim(void_reason)) > 0) OR "
            "(status = 'OPEN' AND voided_at IS NULL AND "
            "voided_by IS NULL AND void_reason IS NULL)",
            name="ck_student_fee_charge_void_state",
        ),
        db.CheckConstraint(
            "length(trim(fee_code)) > 0",
            name="ck_student_fee_charge_code_nonblank",
        ),
        db.CheckConstraint(
            "length(trim(item_code)) > 0",
            name="ck_student_fee_charge_item_code_nonblank",
        ),
        db.CheckConstraint(
            "length(trim(item_name)) > 0",
            name="ck_student_fee_charge_item_name_nonblank",
        ),
        db.Index(
            "uq_student_fee_charge_department_item",
            "student_id",
            "department_id",
            "academic_year_id",
            "semester_id",
            "fee_code",
            "item_code",
            unique=True,
            postgresql_where=db.text("course_offering_id IS NULL"),
            sqlite_where=db.text("course_offering_id IS NULL"),
        ),
        db.Index(
            "uq_student_fee_charge_offering_item",
            "student_id",
            "department_id",
            "academic_year_id",
            "semester_id",
            "course_offering_id",
            "fee_code",
            "item_code",
            unique=True,
            postgresql_where=db.text("course_offering_id IS NOT NULL"),
            sqlite_where=db.text("course_offering_id IS NOT NULL"),
        ),
        db.Index(
            "ix_student_fee_charge_student_period",
            "student_id",
            "academic_year_id",
            "semester_id",
            "status",
        ),
    )

    student_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )

    fee_structure_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("fee_structures.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    fee_structure_item_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("fee_structure_items.id", ondelete="RESTRICT"),
        nullable=False,
    )

    department_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
    )

    academic_year_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )

    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=False,
    )

    course_offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id", ondelete="RESTRICT"),
        nullable=True,
    )

    fee_code = db.Column(
        db.String(40),
        nullable=False,
    )

    item_code = db.Column(
        db.String(40),
        nullable=False,
    )

    item_name = db.Column(
        db.String(100),
        nullable=False,
    )

    item_description = db.Column(
        db.Text,
        nullable=True,
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    currency_code = db.Column(
        db.String(3),
        nullable=False,
    )

    due_date = db.Column(
        db.Date,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="OPEN",
        server_default="OPEN",
    )

    voided_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    voided_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    void_reason = db.Column(
        db.String(500),
        nullable=True,
    )

    student = db.relationship("Student", lazy="selectin")
    fee_structure = db.relationship("FeeStructure", lazy="selectin")
    fee_structure_item = db.relationship(
        "FeeStructureItem",
        lazy="selectin",
    )
    voiding_user = db.relationship("User", lazy="selectin")
    adjustments = db.relationship(
        "FeeAdjustment",
        back_populates="charge",
        lazy="selectin",
        order_by="FeeAdjustment.created_at",
    )

    @property
    def balance_due(self):
        if self.status != "OPEN":
            return Decimal("0.00")
        credits = sum(
            (
                adjustment.amount
                for adjustment in self.adjustments
                if adjustment.status == "ACTIVE"
            ),
            Decimal("0.00"),
        )
        return max(self.amount - credits, Decimal("0.00"))


class FeeAdjustment(UUIDMixin, BaseModel):
    __tablename__ = "fee_adjustments"

    __table_args__ = (
        db.CheckConstraint(
            "amount > 0",
            name="ck_fee_adjustment_amount",
        ),
        db.CheckConstraint(
            "kind IN ('SCHOLARSHIP', 'CONCESSION')",
            name="ck_fee_adjustment_kind",
        ),
        db.CheckConstraint(
            "(kind = 'SCHOLARSHIP' AND scholarship_award_id IS NOT NULL) OR "
            "(kind = 'CONCESSION' AND scholarship_award_id IS NULL)",
            name="ck_fee_adjustment_source",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'VOID')",
            name="ck_fee_adjustment_status",
        ),
        db.CheckConstraint(
            "(status = 'VOID' AND voided_at IS NOT NULL "
            "AND voided_by IS NOT NULL AND void_reason IS NOT NULL "
            "AND length(trim(void_reason)) > 0) OR "
            "(status = 'ACTIVE' AND voided_at IS NULL "
            "AND voided_by IS NULL AND void_reason IS NULL)",
            name="ck_fee_adjustment_void_state",
        ),
        db.CheckConstraint(
            "length(trim(reason)) > 0",
            name="ck_fee_adjustment_reason_nonblank",
        ),
        db.Index(
            "uq_fee_adjustment_active_award_charge",
            "scholarship_award_id",
            "charge_id",
            unique=True,
            postgresql_where=db.text(
                "scholarship_award_id IS NOT NULL AND status = 'ACTIVE'"
            ),
            sqlite_where=db.text(
                "scholarship_award_id IS NOT NULL AND status = 'ACTIVE'"
            ),
        ),
        db.Index(
            "ix_fee_adjustment_charge_status",
            "charge_id",
            "status",
        ),
    )

    charge_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("student_fee_charges.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scholarship_award_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("scholarship_awards.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    kind = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.String(1000), nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )
    created_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    voided_at = db.Column(db.DateTime(timezone=True), nullable=True)
    voided_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    void_reason = db.Column(db.String(500), nullable=True)

    charge = db.relationship(
        "StudentFeeCharge",
        back_populates="adjustments",
        lazy="selectin",
    )
    scholarship_award = db.relationship(
        "ScholarshipAward",
        lazy="selectin",
    )
    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
    )
    voiding_user = db.relationship(
        "User",
        foreign_keys=[voided_by],
        lazy="selectin",
    )


class FeeInvoice(UUIDMixin, BaseModel):
    __tablename__ = "fee_invoices"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ISSUED', 'VOID')",
            name="ck_fee_invoice_status",
        ),
        db.CheckConstraint(
            "total_amount > 0",
            name="ck_fee_invoice_total_amount",
        ),
        db.CheckConstraint(
            "length(trim(invoice_number)) > 0",
            name="ck_fee_invoice_number_nonblank",
        ),
        db.CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_fee_invoice_currency_code",
        ),
        db.CheckConstraint(
            "(status = 'VOID' AND voided_at IS NOT NULL "
            "AND voided_by IS NOT NULL AND void_reason IS NOT NULL "
            "AND length(trim(void_reason)) > 0) OR "
            "(status = 'ISSUED' AND voided_at IS NULL "
            "AND voided_by IS NULL AND void_reason IS NULL)",
            name="ck_fee_invoice_void_state",
        ),
        db.Index(
            "ix_fee_invoice_student_period",
            "student_id",
            "academic_year_id",
            "semester_id",
            "status",
            "issued_at",
        ),
    )

    invoice_number = db.Column(db.String(48), nullable=False, unique=True)
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
        index=True,
    )
    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    currency_code = db.Column(db.String(3), nullable=False)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    issued_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    issued_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    due_date = db.Column(db.Date, nullable=True)
    pdf_object_key = db.Column(db.String(500), nullable=False, unique=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="ISSUED",
        server_default="ISSUED",
    )
    voided_at = db.Column(db.DateTime(timezone=True), nullable=True)
    voided_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    void_reason = db.Column(db.String(500), nullable=True)

    student = db.relationship("Student", lazy="selectin")
    academic_year = db.relationship("AcademicYear", lazy="selectin")
    semester = db.relationship("Semester", lazy="selectin")
    issuer = db.relationship(
        "User",
        foreign_keys=[issued_by],
        lazy="selectin",
    )
    voiding_user = db.relationship(
        "User",
        foreign_keys=[voided_by],
        lazy="selectin",
    )
    lines = db.relationship(
        "FeeInvoiceLine",
        back_populates="invoice",
        lazy="selectin",
        order_by="FeeInvoiceLine.created_at",
    )
    payments = db.relationship(
        "FeePayment",
        back_populates="invoice",
        lazy="selectin",
        order_by="FeePayment.received_at",
    )

    @property
    def amount_paid(self):
        return sum(
            (payment.amount for payment in self.payments),
            Decimal("0.00"),
        )

    @property
    def balance_due(self):
        if self.status == "VOID":
            return Decimal("0.00")
        return max(
            self.total_amount - self.amount_paid,
            Decimal("0.00"),
        )

    @property
    def payment_status(self):
        if self.status == "VOID":
            return "VOID"
        if self.amount_paid == 0:
            return "UNPAID"
        if self.amount_paid >= self.total_amount:
            return "PAID"
        return "PARTIALLY_PAID"


class FeeInvoiceLine(UUIDMixin, BaseModel):
    __tablename__ = "fee_invoice_lines"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ACTIVE', 'VOID')",
            name="ck_fee_invoice_line_status",
        ),
        db.CheckConstraint(
            "gross_amount > 0 AND adjustment_amount >= 0 "
            "AND amount_due >= 0 AND gross_amount >= adjustment_amount "
            "AND amount_due = gross_amount - adjustment_amount",
            name="ck_fee_invoice_line_amounts",
        ),
        db.CheckConstraint(
            "length(trim(fee_code)) > 0 AND length(trim(item_code)) > 0 "
            "AND length(trim(item_name)) > 0",
            name="ck_fee_invoice_line_snapshot_nonblank",
        ),
        db.Index(
            "uq_fee_invoice_line_active_charge",
            "charge_id",
            unique=True,
            postgresql_where=db.text("status = 'ACTIVE'"),
            sqlite_where=db.text("status = 'ACTIVE'"),
        ),
        db.Index(
            "ix_fee_invoice_line_invoice_status",
            "invoice_id",
            "status",
        ),
    )

    invoice_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("fee_invoices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    charge_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("student_fee_charges.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    fee_code = db.Column(db.String(40), nullable=False)
    item_code = db.Column(db.String(40), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    item_description = db.Column(db.Text, nullable=True)
    gross_amount = db.Column(db.Numeric(12, 2), nullable=False)
    adjustment_amount = db.Column(db.Numeric(12, 2), nullable=False)
    amount_due = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )

    invoice = db.relationship(
        "FeeInvoice",
        back_populates="lines",
        lazy="selectin",
    )
    charge = db.relationship("StudentFeeCharge", lazy="selectin")


class FeePayment(UUIDMixin, BaseModel):
    __tablename__ = "fee_payments"

    __table_args__ = (
        db.CheckConstraint(
            "amount > 0",
            name="ck_fee_payment_amount",
        ),
        db.CheckConstraint(
            "payment_method IN ('CASH', 'BANK_TRANSFER', 'CHEQUE', 'OTHER')",
            name="ck_fee_payment_method",
        ),
        db.CheckConstraint(
            "length(trim(receipt_number)) > 0",
            name="ck_fee_payment_receipt_number_nonblank",
        ),
        db.CheckConstraint(
            "amount_paid_after >= amount AND balance_after >= 0",
            name="ck_fee_payment_balance_snapshot",
        ),
        db.Index(
            "ix_fee_payment_invoice_received",
            "invoice_id",
            "received_at",
        ),
    )

    invoice_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("fee_invoices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    receipt_number = db.Column(db.String(48), nullable=False, unique=True)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    amount_paid_after = db.Column(db.Numeric(14, 2), nullable=False)
    balance_after = db.Column(db.Numeric(14, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    payment_reference = db.Column(db.String(100), nullable=True)
    received_at = db.Column(db.DateTime(timezone=True), nullable=False)
    recorded_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    pdf_object_key = db.Column(db.String(500), nullable=False, unique=True)

    invoice = db.relationship(
        "FeeInvoice",
        back_populates="payments",
        lazy="selectin",
    )
    recorder = db.relationship("User", lazy="selectin")

    @property
    def currency_code(self):
        return self.invoice.currency_code
