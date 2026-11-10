from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


ASSESSMENT_TYPES = [
    "INTERNAL",
    "MID_SEM",
    "END_SEM",
    "PRACTICAL",
]


class AssessmentCreateSchema(Schema):
    
    offering_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the course offering."
        },
    )

    assessment_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
    )

    assessment_type = fields.String(
        required=True,
        validate=validate.OneOf(ASSESSMENT_TYPES),
    )

    sequence_number = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    max_marks = fields.Decimal(
        required=True,
        as_string=True,
        validate=validate.Range(min=0.01),
    )

    passing_marks = fields.Decimal(
        required=True,
        as_string=True,
        validate=validate.Range(min=0),
    )

    assessment_date = fields.Date(
        required=True,
    )

    description = fields.String(
        required=False,
        allow_none=True,
    )

    @validates_schema
    def validate_marks(self, data, **kwargs):
        max_marks = data.get("max_marks")
        passing_marks = data.get("passing_marks")

        if (
            max_marks is not None
            and passing_marks is not None
            and passing_marks > max_marks
        ):
            raise ValidationError({
                "passing_marks": [
                    "Passing marks cannot exceed maximum marks."
                ]
            })


class AssessmentUpdateSchema(Schema):

    assessment_name = fields.String(
        required=False,
        validate=validate.Length(min=2, max=100),
    )

    assessment_type = fields.String(
        required=False,
        validate=validate.OneOf(ASSESSMENT_TYPES),
    )

    sequence_number = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )

    max_marks = fields.Decimal(
        required=False,
        as_string=True,
        validate=validate.Range(min=0.01),
    )

    passing_marks = fields.Decimal(
        required=False,
        as_string=True,
        validate=validate.Range(min=0),
    )

    assessment_date = fields.Date(
        required=False,
    )

    description = fields.String(
        required=False,
        allow_none=True,
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field must be provided for an update."
            )

    @validates_schema
    def validate_marks(self, data, **kwargs):
        max_marks = data.get("max_marks")
        passing_marks = data.get("passing_marks")

        if (
            max_marks is not None
            and passing_marks is not None
            and passing_marks > max_marks
        ):
            raise ValidationError({
                "passing_marks": [
                    "Passing marks cannot exceed maximum marks."
                ]
            })


class AssessmentCourseSummarySchema(Schema):

    id = fields.UUID(dump_only=True)
    course_code = fields.String(dump_only=True)
    course_name = fields.String(dump_only=True)
    credits = fields.Integer(dump_only=True)


class AssessmentOfferingSummarySchema(Schema):

    id = fields.UUID(dump_only=True)
    section_code = fields.String(dump_only=True)
    capacity = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
    semester_id = fields.UUID(dump_only=True)
    faculty_id = fields.UUID(dump_only=True)


class AssessmentResponseSchema(Schema):

    id = fields.UUID(dump_only=True)
    assessment_name = fields.String(dump_only=True)
    assessment_type = fields.String(dump_only=True)
    sequence_number = fields.Integer(dump_only=True)
    offering_id = fields.UUID(dump_only=True)

    offering = fields.Nested(
        AssessmentOfferingSummarySchema,
        dump_only=True,
    )

    course_id = fields.UUID(dump_only=True)

    course = fields.Nested(
        AssessmentCourseSummarySchema,
        dump_only=True,
    )

    semester = fields.Integer(dump_only=True)
    academic_year = fields.String(dump_only=True)

    max_marks = fields.Decimal(
        as_string=True,
        dump_only=True,
    )

    passing_marks = fields.Decimal(
        as_string=True,
        dump_only=True,
    )

    assessment_date = fields.Date(dump_only=True)

    description = fields.String(
        allow_none=True,
        dump_only=True,
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AssessmentQuerySchema(Schema):

    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    per_page = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )

    offering_id = fields.UUID(
        required=False,
    )

    course_id = fields.UUID(
        required=False,
    )

    assessment_type = fields.String(
        required=False,
        validate=validate.OneOf(ASSESSMENT_TYPES),
    )

    academic_year = fields.String(
        required=False,
        validate=validate.Regexp(
            r"^\d{4}-\d{4}$",
            error="Academic year must use the format YYYY-YYYY.",
        ),
    )

    semester = fields.Integer(
        required=False,
        validate=validate.Range(min=1, max=12),
    )


class AssessmentPaginationMetadataSchema(Schema):

    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class AssessmentPaginatedResponseSchema(Schema):

    items = fields.List(
        fields.Nested(AssessmentResponseSchema),
        dump_only=True,
    )

    pagination = fields.Nested(
        AssessmentPaginationMetadataSchema,
        dump_only=True,
    )