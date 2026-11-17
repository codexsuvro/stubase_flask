from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    validates_schema,
    ValidationError,
)


ASSIGNMENT_STATUSES = [
    "DRAFT",
    "PUBLISHED",
    "CLOSED",
]

SUBMISSION_STATUSES = [
    "SUBMITTED",
    "GRADED",
]

MAX_MARKS_VALUE = 999999.99


class AssignmentCreateSchema(Schema):
    offering_id = fields.UUID(required=True)

    title = fields.String(
        required=True,
        validate=validate.Length(min=3, max=150),
    )

    description = fields.String(allow_none=True)
    instructions = fields.String(allow_none=True)

    max_marks = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(
            min=0.01,
            max=MAX_MARKS_VALUE,
        ),
    )

    available_from = fields.DateTime(required=True)
    due_at = fields.DateTime(required=True)

    allow_late_submissions = fields.Boolean(
        load_default=False
    )

    allow_resubmissions = fields.Boolean(
        load_default=False
    )

    status = fields.String(
        load_default="DRAFT",
        validate=validate.OneOf(ASSIGNMENT_STATUSES),
    )

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value.strip():
            raise ValidationError(
                "Title cannot contain only whitespace."
            )


class AssignmentUpdateSchema(Schema):
    title = fields.String(
        validate=validate.Length(min=3, max=150)
    )

    description = fields.String(allow_none=True)
    instructions = fields.String(allow_none=True)

    max_marks = fields.Decimal(
        as_string=True,
        places=2,
        validate=validate.Range(
            min=0.01,
            max=MAX_MARKS_VALUE,
        ),
    )

    available_from = fields.DateTime()
    due_at = fields.DateTime()

    allow_late_submissions = fields.Boolean()
    allow_resubmissions = fields.Boolean()

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value.strip():
            raise ValidationError(
                "Title cannot contain only whitespace."
            )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field must be provided for an update."
            )


class AssignmentStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(ASSIGNMENT_STATUSES),
    )


class AssignmentQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    per_page = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )

    offering_id = fields.UUID()

    status = fields.String(
        validate=validate.OneOf(ASSIGNMENT_STATUSES)
    )


class MyAssignmentQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    per_page = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )

    offering_id = fields.UUID()


class SubmissionQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )

    per_page = fields.Integer(
        load_default=10,
        validate=validate.Range(min=1, max=100),
    )

    status = fields.String(
        validate=validate.OneOf(SUBMISSION_STATUSES)
    )


class SubmissionPDFUploadSchema(Schema):
    file = fields.Raw(
        required=True,
        metadata={"type": "string", "format": "binary"},
    )


class SubmissionGradeSchema(Schema):
    marks_obtained = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(
            min=0,
            max=MAX_MARKS_VALUE,
        ),
    )

    feedback = fields.String(allow_none=True)


class AssignmentPaginationMetadataSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class AssignmentResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    offering_id = fields.UUID(dump_only=True)
    created_by = fields.UUID(dump_only=True)

    title = fields.String(dump_only=True)
    description = fields.String(
        allow_none=True,
        dump_only=True,
    )
    instructions = fields.String(
        allow_none=True,
        dump_only=True,
    )

    max_marks = fields.Decimal(
        as_string=True,
        dump_only=True,
    )

    available_from = fields.DateTime(dump_only=True)
    due_at = fields.DateTime(dump_only=True)

    allow_late_submissions = fields.Boolean(dump_only=True)
    allow_resubmissions = fields.Boolean(dump_only=True)

    status = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    offering = fields.Method(
        "get_offering",
        dump_only=True,
    )

    def get_offering(self, obj):
        offering = obj.offering

        return {
            "id": str(offering.id),
            "section_code": offering.section_code,
            "course_id": str(offering.course_id),
            "course_code": offering.course.course_code,
            "course_name": offering.course.course_name,
            "semester_id": str(offering.semester_id),
            "semester": offering.semester.semester_number,
            "academic_year": offering.semester.academic_year.name,
            "faculty_id": str(offering.faculty_id),
        }


class SubmissionResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    assignment_id = fields.UUID(dump_only=True)
    student_id = fields.UUID(dump_only=True)

    text_response = fields.String(
        allow_none=True,
        dump_only=True,
        metadata={
            "description": (
                "Legacy response retained for historical submissions. "
                "New submissions must use a PDF."
            )
        },
    )

    pdf_filename = fields.String(
        allow_none=True,
        dump_only=True,
    )

    submitted_at = fields.DateTime(dump_only=True)
    is_late = fields.Boolean(dump_only=True)
    resubmission_count = fields.Integer(dump_only=True)

    status = fields.String(dump_only=True)

    marks_obtained = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )

    feedback = fields.String(
        allow_none=True,
        dump_only=True,
    )

    graded_by = fields.UUID(
        allow_none=True,
        dump_only=True,
    )

    graded_at = fields.DateTime(
        allow_none=True,
        dump_only=True,
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    student = fields.Method(
        "get_student",
        dump_only=True,
    )

    def get_student(self, obj):
        return {
            "id": str(obj.student.id),
            "student_id": obj.student.student_id,
            "first_name": obj.student.first_name,
            "last_name": obj.student.last_name,
        }


class AssignmentPaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(AssignmentResponseSchema),
        dump_only=True,
    )

    pagination = fields.Nested(
        AssignmentPaginationMetadataSchema,
        dump_only=True,
    )


class SubmissionPaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(SubmissionResponseSchema),
        dump_only=True,
    )

    pagination = fields.Nested(
        AssignmentPaginationMetadataSchema,
        dump_only=True,
    )
