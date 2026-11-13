from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


class FacultyWorkloadQuerySchema(Schema):
    semester_id = fields.UUID(required=True)


class FacultyWorkloadPolicyFilterSchema(Schema):
    faculty_id = fields.UUID(
        required=False,
        allow_none=True,
    )

    semester_id = fields.UUID(
        required=False,
        allow_none=True,
    )


class FacultyWorkloadPolicyCreateSchema(Schema):
    faculty_id = fields.UUID(required=True)
    semester_id = fields.UUID(required=True)

    minimum_hours = fields.Decimal(
        required=False,
        load_default=0,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )

    maximum_hours = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(
            min=0.01,
            error="Maximum hours must be greater than zero.",
        ),
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500),
    )

    @validates_schema
    def validate_hour_range(self, data, **kwargs):
        minimum = data.get("minimum_hours", 0)
        maximum = data.get("maximum_hours")

        if maximum is not None and minimum > maximum:
            raise ValidationError(
                "Minimum hours cannot exceed maximum hours."
            )


class FacultyWorkloadPolicyUpdateSchema(Schema):
    minimum_hours = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )

    maximum_hours = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(
            min=0.01,
            error="Maximum hours must be greater than zero.",
        ),
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500),
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field is required."
            )


class FacultyWorkloadPolicyResponseSchema(Schema):
    id = fields.UUID()
    faculty_id = fields.UUID()
    semester_id = fields.UUID()

    minimum_hours = fields.Decimal(
        as_string=True,
        places=2,
    )

    maximum_hours = fields.Decimal(
        as_string=True,
        places=2,
    )

    remarks = fields.String(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class WorkloadSessionBreakdownSchema(Schema):
    session_type = fields.String()
    total_sessions = fields.Integer()

    weekly_hours = fields.Decimal(
        as_string=True,
        places=2,
    )


class WorkloadCourseSchema(Schema):
    offering_id = fields.UUID()
    course_code = fields.String()
    course_name = fields.String()
    section_code = fields.String()
    session_type = fields.String()
    total_sessions = fields.Integer()

    weekly_hours = fields.Decimal(
        as_string=True,
        places=2,
    )


class FacultyWorkloadResponseSchema(Schema):
    faculty_id = fields.UUID()
    faculty_code = fields.String()
    faculty_name = fields.String()
    designation = fields.String()
    department_name = fields.String()

    semester_id = fields.UUID()
    semester_name = fields.String()

    total_sessions = fields.Integer()

    weekly_teaching_hours = fields.Decimal(
        as_string=True,
        places=2,
    )

    session_breakdown = fields.List(
        fields.Nested(WorkloadSessionBreakdownSchema)
    )

    courses = fields.List(
        fields.Nested(WorkloadCourseSchema)
    )

    policy = fields.Nested(
        FacultyWorkloadPolicyResponseSchema,
        allow_none=True,
    )

    workload_status = fields.String()

    remaining_capacity_hours = fields.Decimal(
        as_string=True,
        places=2,
    )