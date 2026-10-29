from marshmallow import Schema, fields, validate


class EnrollmentCreateSchema(Schema):
    student_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the Student profile, not the User account."
        },
    )

    course_id = fields.UUID(
        required=True,
        metadata={"description": "UUID of the course."},
    )

    semester = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=12),
    )

    academic_year = fields.String(
        required=True,
        validate=validate.Regexp(
            r"^\d{4}-\d{4}$",
            error="Academic year must use the format YYYY-YYYY, e.g. 2026-2027.",
        ),
        metadata={"example": "2026-2027"},
    )

    status = fields.String(
        load_default="ENROLLED",
        validate=validate.OneOf(
            ["ENROLLED", "WITHDRAWN", "COMPLETED"]
        ),
    )


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


class EnrollmentResponseSchema(Schema):
    id = fields.UUID(dump_only=True)

    student_id = fields.UUID(dump_only=True)
    course_id = fields.UUID(dump_only=True)

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

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)