from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates,
    validates_schema,
)


FEE_STRUCTURE_STATUSES = ("DRAFT", "ACTIVE", "ARCHIVED")
FEE_CODE_VALIDATOR = validate.Regexp(r"^[A-Z0-9][A-Z0-9_-]{0,39}$")
ITEM_CODE_VALIDATOR = validate.Regexp(r"^[A-Z0-9][A-Z0-9_-]{0,39}$")


class FeeStructureItemInputSchema(Schema):
    item_code = fields.String(
        required=True,
        validate=ITEM_CODE_VALIDATOR,
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    description = fields.String(allow_none=True)
    amount = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        allow_nan=False,
        validate=validate.Range(min=0.01),
    )
    is_mandatory = fields.Boolean(load_default=True)
    sequence_order = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    @validates("name")
    def validate_name(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Name cannot contain only whitespace.")


class FeeStructureCreateSchema(Schema):
    department_id = fields.UUID(required=True)
    academic_year_id = fields.UUID(required=True)
    semester_id = fields.UUID(required=True)
    course_offering_id = fields.UUID(allow_none=True)
    fee_code = fields.String(
        required=True,
        validate=FEE_CODE_VALIDATOR,
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=150),
    )
    description = fields.String(allow_none=True)
    currency_code = fields.String(
        load_default="INR",
        validate=validate.Regexp(r"^[A-Z]{3}$"),
    )
    items = fields.List(
        fields.Nested(FeeStructureItemInputSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @validates("name")
    def validate_name(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Name cannot contain only whitespace.")

    @validates_schema
    def validate_items(self, data, **_kwargs):
        del _kwargs
        items = data.get("items", [])
        codes = [item["item_code"].upper() for item in items]
        sequences = [item["sequence_order"] for item in items]
        errors = {}
        if len(codes) != len(set(codes)):
            errors["items"] = ["Item codes must be unique."]
        if len(sequences) != len(set(sequences)):
            errors["items"] = ["Item sequence numbers must be unique."]
        if errors:
            raise ValidationError(errors)


class FeeStructureUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=150))
    description = fields.String(allow_none=True)
    currency_code = fields.String(validate=validate.Regexp(r"^[A-Z]{3}$"))
    items = fields.List(
        fields.Nested(FeeStructureItemInputSchema),
        validate=validate.Length(min=1),
    )

    @validates("name")
    def validate_name(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Name cannot contain only whitespace.")

    @validates_schema
    def validate_update(self, data, **_kwargs):
        del _kwargs
        if not data:
            raise ValidationError("At least one field must be provided.")
        items = data.get("items")
        if items is None:
            return
        codes = [item["item_code"].upper() for item in items]
        sequences = [item["sequence_order"] for item in items]
        errors = {}
        if len(codes) != len(set(codes)):
            errors["items"] = ["Item codes must be unique."]
        if len(sequences) != len(set(sequences)):
            errors["items"] = ["Item sequence numbers must be unique."]
        if errors:
            raise ValidationError(errors)


class FeeStructureQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    academic_year_id = fields.UUID()
    semester_id = fields.UUID()
    department_id = fields.UUID()
    course_offering_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(FEE_STRUCTURE_STATUSES))


class FeeStructureItemResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    item_code = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(allow_none=True, dump_only=True)
    amount = fields.Decimal(as_string=True, dump_only=True)
    is_mandatory = fields.Boolean(dump_only=True)
    sequence_order = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class FeeStructureResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    department_id = fields.UUID(dump_only=True)
    academic_year_id = fields.UUID(dump_only=True)
    semester_id = fields.UUID(dump_only=True)
    course_offering_id = fields.UUID(allow_none=True, dump_only=True)
    fee_code = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(allow_none=True, dump_only=True)
    version = fields.Integer(dump_only=True)
    currency_code = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    activated_at = fields.DateTime(allow_none=True, dump_only=True)
    archived_at = fields.DateTime(allow_none=True, dump_only=True)
    items = fields.List(
        fields.Nested(FeeStructureItemResponseSchema),
        dump_only=True,
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class FeeStructurePaginationSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class FeeStructurePaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(FeeStructureResponseSchema),
        dump_only=True,
    )
    pagination = fields.Nested(
        FeeStructurePaginationSchema,
        dump_only=True,
    )


class FeeChargeApplySchema(Schema):
    due_date = fields.Date(allow_none=True)


class FeeChargeQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    academic_year_id = fields.UUID()
    semester_id = fields.UUID()
    student_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(("OPEN", "VOID")))


class MyFeeChargeQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    academic_year_id = fields.UUID()
    semester_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(("OPEN", "VOID")))


class FeeChargeResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    student_id = fields.UUID(dump_only=True)
    fee_structure_id = fields.UUID(dump_only=True)
    fee_structure_item_id = fields.UUID(dump_only=True)
    department_id = fields.UUID(dump_only=True)
    academic_year_id = fields.UUID(dump_only=True)
    semester_id = fields.UUID(dump_only=True)
    course_offering_id = fields.UUID(allow_none=True, dump_only=True)
    fee_code = fields.String(dump_only=True)
    item_code = fields.String(dump_only=True)
    item_name = fields.String(dump_only=True)
    item_description = fields.String(allow_none=True, dump_only=True)
    amount = fields.Decimal(as_string=True, dump_only=True)
    balance_due = fields.Decimal(as_string=True, dump_only=True)
    currency_code = fields.String(dump_only=True)
    due_date = fields.Date(allow_none=True, dump_only=True)
    status = fields.String(dump_only=True)
    voided_at = fields.DateTime(allow_none=True, dump_only=True)
    voided_by = fields.UUID(allow_none=True, dump_only=True)
    void_reason = fields.String(allow_none=True, dump_only=True)
    adjustments = fields.List(
        fields.Nested("ScholarshipFeeAdjustmentResponseSchema"),
        dump_only=True,
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class FeeChargeVoidSchema(Schema):
    reason = fields.String(
        required=True,
        validate=validate.Length(min=1, max=500),
    )

    @validates("reason")
    def validate_reason(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Reason cannot contain only whitespace.")


class FeeChargePaginationSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class FeeChargePaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(FeeChargeResponseSchema),
        dump_only=True,
    )
    pagination = fields.Nested(
        FeeChargePaginationSchema,
        dump_only=True,
    )


class FeeChargeApplyResponseSchema(Schema):
    fee_structure_id = fields.UUID(dump_only=True)
    eligible_students = fields.Integer(dump_only=True)
    created_charges = fields.Integer(dump_only=True)
    existing_charges = fields.Integer(dump_only=True)


INVOICE_STATUSES = ("ISSUED", "VOID")


class FeeInvoiceCreateSchema(Schema):
    student_id = fields.UUID(required=True)
    charge_ids = fields.List(
        fields.UUID(),
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    due_date = fields.Date(allow_none=True)

    @validates_schema
    def validate_charge_ids(self, data, **_kwargs):
        del _kwargs
        charge_ids = data.get("charge_ids", [])
        if len(charge_ids) != len(set(charge_ids)):
            raise ValidationError(
                {"charge_ids": ["Charge IDs must be unique."]}
            )


class FeeInvoiceQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    student_id = fields.UUID()
    academic_year_id = fields.UUID()
    semester_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(INVOICE_STATUSES))


class MyFeeInvoiceQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    academic_year_id = fields.UUID()
    semester_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(INVOICE_STATUSES))


class FeeInvoiceLineResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    charge_id = fields.UUID(dump_only=True)
    fee_code = fields.String(dump_only=True)
    item_code = fields.String(dump_only=True)
    item_name = fields.String(dump_only=True)
    item_description = fields.String(allow_none=True, dump_only=True)
    gross_amount = fields.Decimal(as_string=True, dump_only=True)
    adjustment_amount = fields.Decimal(as_string=True, dump_only=True)
    amount_due = fields.Decimal(as_string=True, dump_only=True)
    status = fields.String(dump_only=True)


class FeeInvoiceResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    invoice_number = fields.String(dump_only=True)
    student_id = fields.UUID(dump_only=True)
    academic_year_id = fields.UUID(dump_only=True)
    semester_id = fields.UUID(dump_only=True)
    currency_code = fields.String(dump_only=True)
    total_amount = fields.Decimal(as_string=True, dump_only=True)
    issued_at = fields.DateTime(dump_only=True)
    issued_by = fields.UUID(dump_only=True)
    due_date = fields.Date(allow_none=True, dump_only=True)
    status = fields.String(dump_only=True)
    voided_at = fields.DateTime(allow_none=True, dump_only=True)
    voided_by = fields.UUID(allow_none=True, dump_only=True)
    void_reason = fields.String(allow_none=True, dump_only=True)
    lines = fields.List(
        fields.Nested(FeeInvoiceLineResponseSchema),
        dump_only=True,
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class FeeInvoicePaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(FeeInvoiceResponseSchema),
        dump_only=True,
    )
    pagination = fields.Nested(
        FeeChargePaginationSchema,
        dump_only=True,
    )


class FeeInvoiceVoidSchema(Schema):
    reason = fields.String(
        required=True,
        validate=validate.Length(min=1, max=500),
    )

    @validates("reason")
    def validate_reason(self, value, **_kwargs):
        del _kwargs
        if not value.strip():
            raise ValidationError("Reason cannot contain only whitespace.")
