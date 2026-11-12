from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


class GradeScaleCreateSchema(Schema):
    letter_grade = fields.String(
        required=True,
        validate=validate.Length(min=1, max=5),
    )

    min_percentage = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0, max=100),
    )

    max_percentage = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0, max=100),
    )

    grade_point = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )

    is_passing = fields.Boolean(
        required=True,
    )

    @validates_schema
    def validate_range(self, data, **kwargs):
        if (
            data.get("min_percentage") is not None
            and data.get("max_percentage") is not None
            and data["min_percentage"] > data["max_percentage"]
        ):
            raise ValidationError(
                "Minimum percentage cannot exceed maximum percentage."
            )


class GradingSchemeCreateSchema(Schema):
    scheme_name = fields.String(
        required=True,
        validate=validate.Length(min=3, max=100),
    )

    description = fields.String(
        allow_none=True,
    )

    grade_scales = fields.List(
        fields.Nested(GradeScaleCreateSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class GradingSchemeUpdateSchema(Schema):
    scheme_name = fields.String(
        required=False,
        validate=validate.Length(min=3, max=100),
    )

    description = fields.String(
        required=False,
        allow_none=True,
    )

    status = fields.String(
        required=False,
        validate=validate.OneOf(["ACTIVE", "INACTIVE"]),
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field must be provided."
            )


class GradeScaleResponseSchema(Schema):
    id = fields.UUID()
    letter_grade = fields.String()
    min_percentage = fields.Decimal(as_string=True, places=2)
    max_percentage = fields.Decimal(as_string=True, places=2)
    grade_point = fields.Decimal(as_string=True, places=2)
    is_passing = fields.Boolean()


class GradingSchemeResponseSchema(Schema):
    id = fields.UUID()
    scheme_name = fields.String()
    description = fields.String(allow_none=True)
    status = fields.String()
    grade_scales = fields.List(
        fields.Nested(GradeScaleResponseSchema)
    )
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class CourseGradeCalculateSchema(Schema):
    enrollment_id = fields.UUID(required=True)
    grading_scheme_id = fields.UUID(required=True)


class CourseGradeResponseSchema(Schema):
    id = fields.UUID()
    enrollment_id = fields.UUID()
    grading_scheme_id = fields.UUID()
    total_marks = fields.Decimal(as_string=True, places=2)
    percentage = fields.Decimal(as_string=True, places=2)
    letter_grade = fields.String(allow_none=True)
    grade_point = fields.Decimal(as_string=True, places=2)
    result_status = fields.String()
    publication_status = fields.String()
    published_at = fields.DateTime(allow_none=True)


class TranscriptCourseSchema(Schema):
    course_code = fields.String()
    course_name = fields.String()
    credits = fields.Integer()
    academic_year = fields.String()
    semester = fields.Integer()
    percentage = fields.Decimal(as_string=True, places=2)
    letter_grade = fields.String()
    grade_point = fields.Decimal(as_string=True, places=2)
    result_status = fields.String()


class TranscriptResponseSchema(Schema):
    student_id = fields.String()
    student_name = fields.String()
    courses = fields.List(
        fields.Nested(TranscriptCourseSchema)
    )
    total_credits = fields.Integer()
    earned_credits = fields.Integer()
    cgpa = fields.Decimal(as_string=True, places=2)