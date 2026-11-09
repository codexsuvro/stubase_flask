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


# -------------------------------
# Nested Response Schemas
# -------------------------------

class ResultCourseSchema(Schema):

    id = fields.UUID()
    course_code = fields.String()
    course_name = fields.String()
    credits = fields.Integer()
    semester = fields.Integer()


class ResultAssessmentSchema(Schema):

    id = fields.UUID()
    assessment_name = fields.String()
    assessment_type = fields.String()
    sequence_number = fields.Integer()
    academic_year = fields.String()
    semester = fields.Integer()
    max_marks = fields.Decimal(as_string=True, places=2)
    passing_marks = fields.Decimal(as_string=True, places=2)
    assessment_date = fields.Date()

    course = fields.Nested(ResultCourseSchema)


class ResultStudentSchema(Schema):

    id = fields.UUID()
    student_id = fields.String()
    first_name = fields.String()
    last_name = fields.String()


class ResultEnrollmentSchema(Schema):

    id = fields.UUID()
    academic_year = fields.String()
    semester = fields.Integer()
    status = fields.String()

    student = fields.Nested(ResultStudentSchema)


# -------------------------------
# Main Result Response
# -------------------------------

class AssessmentResultResponseSchema(Schema):

    id = fields.UUID(dump_only=True)

    assessment_id = fields.UUID()
    enrollment_id = fields.UUID()

    assessment = fields.Nested(
        ResultAssessmentSchema,
        dump_only=True,
    )

    enrollment = fields.Nested(
        ResultEnrollmentSchema,
        dump_only=True,
    )

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


class AssessmentAnalyticsResponseSchema(Schema):

    total_assessments = fields.Integer()
    total_students = fields.Integer()

    total_marks_obtained = fields.Decimal(
        as_string=True,
        places=2,
    )

    total_max_marks = fields.Decimal(
        as_string=True,
        places=2,
    )

    percentage = fields.Decimal(
        as_string=True,
        places=2,
    )

    average_marks = fields.Decimal(
        as_string=True,
        places=2,
    )

    highest_marks = fields.Decimal(
        as_string=True,
        places=2,
    )

    lowest_marks = fields.Decimal(
        as_string=True,
        places=2,
    )

    passed = fields.Integer()
    failed = fields.Integer()