from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class AttendanceCreateSchema(Schema):
    enrollment_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the existing Enrollment record."
        },
    )

    attendance_date = fields.Date(
        required=False,
        allow_none=False,
        metadata={"example": "2026-11-02"},
    )

    status = fields.String(
        required=True,
        validate=validate.OneOf(
            ["PRESENT", "ABSENT", "LATE"]
        ),
        metadata={"example": "PRESENT"},
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )


class AttendanceResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    enrollment_id = fields.UUID(dump_only=True)
    attendance_date = fields.Date(dump_only=True)
    status = fields.String(dump_only=True)
    remarks = fields.String(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AttendanceSummarySchema(Schema):
    enrollment_id = fields.UUID(dump_only=True)
    total_classes = fields.Integer(dump_only=True)
    present_count = fields.Integer(dump_only=True)
    absent_count = fields.Integer(dump_only=True)
    late_count = fields.Integer(dump_only=True)
    attendance_percentage = fields.Float(dump_only=True)
    

class AttendanceUpdateSchema(Schema):

    status = fields.String(
        required=False,
        validate=validate.OneOf(
            ["PRESENT", "ABSENT", "LATE"]
        ),
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )

    @validates_schema
    def validate_update(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field (status or remarks) must be provided."
            )


class AttendanceAuditResponseSchema(Schema):

    id = fields.UUID(dump_only=True)
    attendance_id = fields.UUID(dump_only=True)
    changed_by_user_id = fields.UUID(dump_only=True)

    previous_status = fields.String(dump_only=True)
    new_status = fields.String(dump_only=True)

    previous_remarks = fields.String(
        allow_none=True,
        dump_only=True,
    )

    new_remarks = fields.String(
        allow_none=True,
        dump_only=True,
    )

    created_at = fields.DateTime(dump_only=True)


class AttendanceShortageSchema(Schema):

    enrollment_id = fields.UUID(dump_only=True)
    attendance_percentage = fields.Float(dump_only=True)
    minimum_required_percentage = fields.Float(dump_only=True)
    shortage_detected = fields.Boolean(dump_only=True)
    total_classes = fields.Integer(dump_only=True)