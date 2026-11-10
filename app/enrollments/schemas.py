
from marshmallow import Schema, fields, validate


class EnrollmentCreateSchema(Schema):

    student_id = fields.UUID(required=True)

    offering_id = fields.UUID(required=True)


class EnrollmentStudentSummarySchema(Schema):
    id = fields.UUID(dump_only=True)
    student_id = fields.String(dump_only=True)
    first_name = fields.String(dump_only=True)
    last_name = fields.String(dump_only=True)


class EnrollmentCourseSummarySchema(Schema):
    id = fields.UUID(dump_only=True)
    course_code = fields.String(dump_only=True)
    course_name = fields.String(dump_only=True)
    credits = fields.Integer(dump_only=True)
    semester = fields.Integer(dump_only=True)

class EnrollmentOfferingSummarySchema(Schema):
    id = fields.UUID(dump_only=True)
    section_code = fields.String(dump_only=True)
    capacity = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
    semester_id = fields.UUID(dump_only=True)
    faculty_id = fields.UUID(dump_only=True)

class EnrollmentResponseSchema(Schema):
    id = fields.UUID(dump_only=True)

    student_id = fields.UUID(dump_only=True)
    course_id = fields.UUID(dump_only=True)
    offering_id = fields.UUID(dump_only=True)

    semester = fields.Integer(dump_only=True)
    academic_year = fields.String(dump_only=True)
    status = fields.String(dump_only=True)

    student = fields.Nested(
        EnrollmentStudentSummarySchema,
        dump_only=True,
    )

    course = fields.Nested(
        EnrollmentCourseSummarySchema,
        dump_only=True,
    )

    offering = fields.Nested(
        EnrollmentOfferingSummarySchema,
        dump_only=True,
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class EnrollmentQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    per_page = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )

    student_id = fields.UUID(required=False)

    course_id = fields.UUID(required=False)

    offering_id = fields.UUID(required=False)

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

    status = fields.String(
        required=False,
        validate=validate.OneOf(
            ["ENROLLED", "WITHDRAWN", "COMPLETED"],
        ),
    )


class EnrollmentPaginationMetadataSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class EnrollmentPaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(EnrollmentResponseSchema),
        dump_only=True,
    )

    pagination = fields.Nested(
        EnrollmentPaginationMetadataSchema,
        dump_only=True,
    )