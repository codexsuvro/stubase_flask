from decimal import Decimal

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates,
)


PROGRAM_STATUSES = ("DRAFT", "OPEN", "CLOSED", "ARCHIVED")
APPLICATION_STATUSES = ("SUBMITTED", "APPROVED", "REJECTED", "WITHDRAWN")
AWARD_TYPES = ("FIXED", "PERCENTAGE")
MAX_MONEY_AMOUNT = Decimal("9999999999.99")


class ScholarshipProgramCreateSchema(Schema):
    code = fields.String(
        required=True,
        validate=validate.Regexp(r"^[A-Z0-9][A-Z0-9_-]{0,39}$"),
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=150),
    )
    description = fields.String(allow_none=True)
    academic_year_id = fields.UUID(required=True)
    semester_id = fields.UUID(allow_none=True)
    department_id = fields.UUID(allow_none=True)
    application_open_at = fields.DateTime(required=True)
    application_close_at = fields.DateTime(required=True)
    min_cgpa = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0, max=100),
    )
    award_type = fields.String(
        required=True,
        validate=validate.OneOf(AWARD_TYPES),
    )
    award_value = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    max_award_amount = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    total_budget_amount = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    max_recipients = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=1),
    )
    currency_code = fields.String(
        load_default="INR",
        validate=validate.Regexp(r"^[A-Z]{3}$"),
    )

    @validates("name")
    def validate_name(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Name cannot contain only whitespace.")

    @validates("code")
    def normalize_code(self, value, **_kwargs):
        del _kwargs
        if value != value.strip().upper():
            raise ValidationError("Code must be uppercase and have no surrounding whitespace.")

    @validates("currency_code")
    def normalize_currency(self, value, **_kwargs):
        del _kwargs
        if value != value.strip().upper():
            raise ValidationError(
                "Currency code must be uppercase and have no surrounding whitespace."
            )

    @validates("award_type")
    def normalize_award_type(self, value, **_kwargs):
        del _kwargs
        if value != value.strip().upper():
            raise ValidationError("Award type must be uppercase.")


class ScholarshipProgramUpdateSchema(Schema):
    code = fields.String(
        validate=validate.Regexp(r"^[A-Z0-9][A-Z0-9_-]{0,39}$"),
    )
    name = fields.String(validate=validate.Length(min=1, max=150))
    description = fields.String(allow_none=True)
    academic_year_id = fields.UUID()
    semester_id = fields.UUID(allow_none=True)
    department_id = fields.UUID(allow_none=True)
    application_open_at = fields.DateTime()
    application_close_at = fields.DateTime()
    min_cgpa = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0, max=100),
    )
    award_type = fields.String(validate=validate.OneOf(AWARD_TYPES))
    award_value = fields.Decimal(
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    max_award_amount = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    total_budget_amount = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    max_recipients = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=1),
    )
    currency_code = fields.String(validate=validate.Regexp(r"^[A-Z]{3}$"))

    @validates("name")
    def validate_name(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Name cannot contain only whitespace.")

    @validates("code")
    def normalize_code(self, value, **_kwargs):
        del _kwargs
        if value != value.strip().upper():
            raise ValidationError("Code must be uppercase and have no surrounding whitespace.")

    @validates("currency_code")
    def normalize_currency(self, value, **_kwargs):
        del _kwargs
        if value != value.strip().upper():
            raise ValidationError(
                "Currency code must be uppercase and have no surrounding whitespace."
            )


class ScholarshipProgramQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    academic_year_id = fields.UUID()
    semester_id = fields.UUID()
    department_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(PROGRAM_STATUSES))


class PageQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )


class MyScholarshipApplicationQuerySchema(PageQuerySchema):
    status = fields.String(validate=validate.OneOf(APPLICATION_STATUSES))


class MyScholarshipAwardQuerySchema(PageQuerySchema):
    status = fields.String(validate=validate.OneOf(("ACTIVE", "REVOKED")))


class ScholarshipProgramResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    code = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(allow_none=True, dump_only=True)
    academic_year_id = fields.UUID(dump_only=True)
    semester_id = fields.UUID(allow_none=True, dump_only=True)
    department_id = fields.UUID(allow_none=True, dump_only=True)
    application_open_at = fields.DateTime(dump_only=True)
    application_close_at = fields.DateTime(dump_only=True)
    min_cgpa = fields.Decimal(as_string=True, allow_none=True, dump_only=True)
    award_type = fields.String(dump_only=True)
    award_value = fields.Decimal(as_string=True, dump_only=True)
    max_award_amount = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )
    total_budget_amount = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )
    max_recipients = fields.Integer(allow_none=True, dump_only=True)
    currency_code = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    opened_at = fields.DateTime(allow_none=True, dump_only=True)
    closed_at = fields.DateTime(allow_none=True, dump_only=True)
    archived_at = fields.DateTime(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PaginationSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class ScholarshipProgramPaginatedResponseSchema(Schema):
    items = fields.List(fields.Nested(ScholarshipProgramResponseSchema))
    pagination = fields.Nested(PaginationSchema)


class ScholarshipApplicationCreateSchema(Schema):
    statement = fields.String(
        required=True,
        validate=validate.Length(min=1, max=5000),
    )

    @validates("statement")
    def validate_statement(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Statement cannot contain only whitespace.")


class ScholarshipApplicationDocumentUploadSchema(Schema):
    file = fields.Raw(
        required=True,
        metadata={"type": "string", "format": "binary"},
    )


class ScholarshipApplicationDocumentResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    application_id = fields.UUID(dump_only=True)
    filename = fields.String(dump_only=True)
    uploaded_at = fields.DateTime(dump_only=True)
    uploaded_by = fields.UUID(dump_only=True)


class ScholarshipApplicationDocumentCollectionResponseSchema(Schema):
    items = fields.List(
        fields.Nested(ScholarshipApplicationDocumentResponseSchema),
        dump_only=True,
    )


class ScholarshipApplicationQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    program_id = fields.UUID()
    student_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(APPLICATION_STATUSES))


class ScholarshipApplicationResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    program_id = fields.UUID(dump_only=True)
    student_id = fields.UUID(dump_only=True)
    statement = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    submitted_at = fields.DateTime(dump_only=True)
    decided_at = fields.DateTime(allow_none=True, dump_only=True)
    decided_by = fields.UUID(allow_none=True, dump_only=True)
    decision_notes = fields.String(allow_none=True, dump_only=True)
    award = fields.Nested(
        "ScholarshipAwardResponseSchema",
        allow_none=True,
        dump_only=True,
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ScholarshipApplicationPaginatedResponseSchema(Schema):
    items = fields.List(fields.Nested(ScholarshipApplicationResponseSchema))
    pagination = fields.Nested(PaginationSchema)


class ScholarshipApproveSchema(Schema):
    award_value = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    award_reason = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000),
    )
    decision_notes = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000),
    )


class ScholarshipRejectSchema(Schema):
    decision_notes = fields.String(
        required=True,
        validate=validate.Length(min=1, max=1000),
    )

    @validates("decision_notes")
    def validate_decision_notes(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("A rejection reason is required.")


class ScholarshipAwardResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    application_id = fields.UUID(dump_only=True)
    program_id = fields.UUID(dump_only=True)
    student_id = fields.UUID(dump_only=True)
    academic_year_id = fields.UUID(dump_only=True)
    semester_id = fields.UUID(allow_none=True, dump_only=True)
    department_id = fields.UUID(allow_none=True, dump_only=True)
    award_type = fields.String(dump_only=True)
    award_value = fields.Decimal(as_string=True, dump_only=True)
    max_award_amount = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )
    currency_code = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    awarded_at = fields.DateTime(dump_only=True)
    awarded_by = fields.UUID(dump_only=True)
    award_reason = fields.String(allow_none=True, dump_only=True)
    revoked_at = fields.DateTime(allow_none=True, dump_only=True)
    revoked_by = fields.UUID(allow_none=True, dump_only=True)
    revoked_reason = fields.String(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ScholarshipAwardPaginatedResponseSchema(Schema):
    items = fields.List(fields.Nested(ScholarshipAwardResponseSchema))
    pagination = fields.Nested(PaginationSchema)


class ScholarshipAwardQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    student_id = fields.UUID()
    program_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(("ACTIVE", "REVOKED")))


class ScholarshipAwardApplyResponseSchema(Schema):
    award_id = fields.UUID(dump_only=True)
    created_adjustments = fields.List(
        fields.Nested("ScholarshipFeeAdjustmentResponseSchema"),
        dump_only=True,
    )
    skipped_charges = fields.Integer(dump_only=True)
    total_applied = fields.Decimal(as_string=True, dump_only=True)
    remaining_fixed_award = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )


class ConcessionCreateSchema(Schema):
    charge_id = fields.UUID(required=True)
    amount = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01, max=MAX_MONEY_AMOUNT),
    )
    reason = fields.String(
        required=True,
        validate=validate.Length(min=1, max=1000),
    )

    @validates("reason")
    def validate_reason(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Reason cannot contain only whitespace.")


class FeeAdjustmentVoidSchema(Schema):
    reason = fields.String(
        required=True,
        validate=validate.Length(min=1, max=500),
    )

    @validates("reason")
    def validate_reason(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Reason cannot contain only whitespace.")


class ScholarshipFeeAdjustmentResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    charge_id = fields.UUID(dump_only=True)
    scholarship_award_id = fields.UUID(allow_none=True, dump_only=True)
    kind = fields.String(dump_only=True)
    amount = fields.Decimal(as_string=True, dump_only=True)
    reason = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    created_by = fields.UUID(dump_only=True)
    voided_at = fields.DateTime(allow_none=True, dump_only=True)
    voided_by = fields.UUID(allow_none=True, dump_only=True)
    void_reason = fields.String(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ScholarshipFeeAdjustmentQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    student_id = fields.UUID()
    charge_id = fields.UUID()
    kind = fields.String(validate=validate.OneOf(("SCHOLARSHIP", "CONCESSION")))
    status = fields.String(validate=validate.OneOf(("ACTIVE", "VOID")))


class ScholarshipFeeAdjustmentPaginatedResponseSchema(Schema):
    items = fields.List(fields.Nested(ScholarshipFeeAdjustmentResponseSchema))
    pagination = fields.Nested(PaginationSchema)
