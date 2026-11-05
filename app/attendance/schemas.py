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
    

class StudentAttendanceSummarySchema(Schema):
    enrollment_id = fields.UUID(dump_only=True)
    course_code = fields.String(dump_only=True)
    course_name = fields.String(dump_only=True)
    academic_year = fields.String(dump_only=True)

    total_classes = fields.Integer(dump_only=True)
    present_count = fields.Integer(dump_only=True)
    absent_count = fields.Integer(dump_only=True)
    late_count = fields.Integer(dump_only=True)
    attendance_percentage = fields.Float(dump_only=True)


class StudentAttendanceShortageSchema(Schema):
    enrollment_id = fields.UUID(dump_only=True)
    course_code = fields.String(dump_only=True)
    course_name = fields.String(dump_only=True)

    attendance_percentage = fields.Float(dump_only=True)
    minimum_required_percentage = fields.Float(dump_only=True)
    shortage_detected = fields.Boolean(dump_only=True)
    total_classes = fields.Integer(dump_only=True)
    
    
class AttendancePaginationMetadataSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class AttendancePaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(AttendanceResponseSchema),
        dump_only=True,
    )
    pagination = fields.Nested(
        AttendancePaginationMetadataSchema,
        dump_only=True,
    )
    

class AttendanceQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    per_page = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )

    status = fields.String(
        required=False,
        validate=validate.OneOf(["PRESENT", "ABSENT", "LATE"]),
    )

    course_code = fields.String(
        required=False,
        validate=validate.Length(min=1, max=20),
    )

    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False)
    student_id = fields.UUID(required=False)

    @validates_schema
    def validate_date_range(self, data, **kwargs):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise ValidationError(
                "start_date cannot be later than end_date."
            )