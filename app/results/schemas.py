from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


class AssessmentResultCreateSchema(Schema):

    assessment_id = fields.UUID(required=True)
    enrollment_id = fields.UUID(required=True)

    marks_obtained = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(
            min=0,
            error="Marks obtained cannot be negative.",
        ),
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )


class AssessmentResultUpdateSchema(Schema):

    marks_obtained = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(
            min=0,
            error="Marks obtained cannot be negative.",
        ),
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field must be provided."
            )


class AssessmentResultQuerySchema(Schema):

    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    per_page = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )

    assessment_id = fields.UUID(required=False)
    enrollment_id = fields.UUID(required=False)
    course_id = fields.UUID(required=False)


class AssessmentResultResponseSchema(Schema):

    id = fields.UUID(dump_only=True)
    assessment_id = fields.UUID()
    enrollment_id = fields.UUID()

    marks_obtained = fields.Decimal(
        as_string=True,
        places=2,
    )

    remarks = fields.String(allow_none=True)
    graded_by = fields.UUID()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class AssessmentResultPaginatedResponseSchema(Schema):

    items = fields.List(
        fields.Nested(AssessmentResultResponseSchema),
    )

    total = fields.Integer()
    page = fields.Integer()
    per_page = fields.Integer()
    pages = fields.Integer()
    
    
