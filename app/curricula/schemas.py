from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


CURRICULUM_STATUSES = ["DRAFT", "PUBLISHED", "ARCHIVED"]
SYLLABUS_STATUSES = ["DRAFT", "PUBLISHED", "ARCHIVED"]
MAX_TEXT_LENGTH = 10000


class NonBlankSchema(Schema):
    @validates_schema
    def validate_non_blank_fields(self, data, **kwargs):
        non_blank_fields = (
            "curriculum_code",
            "curriculum_name",
            "program_name",
            "title",
            "outcome_code",
        )
        errors = {
            field_name: ["Value cannot contain only whitespace."]
            for field_name in non_blank_fields
            if data.get(field_name) is not None
            and not data[field_name].strip()
        }
        if errors:
            raise ValidationError(errors)


class CurriculumCreateSchema(NonBlankSchema):
    department_id = fields.UUID(required=True)
    academic_year_id = fields.UUID(required=True)
    curriculum_code = fields.String(required=True, validate=validate.Length(min=1, max=30))
    curriculum_name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    program_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    version = fields.Integer(load_default=1, validate=validate.Range(min=1))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    effective_from = fields.Date(required=True)
    effective_until = fields.Date(allow_none=True)

    @validates_schema
    def validate_effective_dates(self, data, **kwargs):
        end = data.get("effective_until")
        if end is not None and data["effective_from"] >= end:
            raise ValidationError({
                "effective_until": ["Must be later than effective_from."]
            })


class CurriculumUpdateSchema(NonBlankSchema):
    department_id = fields.UUID()
    academic_year_id = fields.UUID()
    curriculum_code = fields.String(validate=validate.Length(min=1, max=30))
    curriculum_name = fields.String(validate=validate.Length(min=1, max=150))
    program_name = fields.String(validate=validate.Length(min=1, max=100))
    version = fields.Integer(validate=validate.Range(min=1))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    effective_from = fields.Date()
    effective_until = fields.Date(allow_none=True)

    @validates_schema
    def validate_update(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided.")
        start = data.get("effective_from")
        end = data.get("effective_until")
        if start is not None and end is not None and start >= end:
            raise ValidationError({
                "effective_until": ["Must be later than effective_from."]
            })


class CurriculumQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))
    department_id = fields.UUID()
    academic_year_id = fields.UUID()
    status = fields.String(validate=validate.OneOf(CURRICULUM_STATUSES))
    curriculum_code = fields.String(validate=validate.Length(max=30))


class CurriculumResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    department_id = fields.UUID(dump_only=True)
    academic_year_id = fields.UUID(dump_only=True)
    curriculum_code = fields.String(dump_only=True)
    curriculum_name = fields.String(dump_only=True)
    program_name = fields.String(dump_only=True)
    version = fields.Integer(dump_only=True)
    description = fields.String(allow_none=True, dump_only=True)
    effective_from = fields.Date(dump_only=True)
    effective_until = fields.Date(allow_none=True, dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CurriculumPaginationMetadataSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class CurriculumPaginatedResponseSchema(Schema):
    items = fields.List(fields.Nested(CurriculumResponseSchema), dump_only=True)
    pagination = fields.Nested(
        CurriculumPaginationMetadataSchema,
        dump_only=True,
    )


class CurriculumCourseCreateSchema(Schema):
    course_id = fields.UUID(required=True)
    semester_id = fields.UUID(required=True)
    sequence_order = fields.Integer(required=True, validate=validate.Range(min=1))
    credits_override = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    required_hours = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )


class CurriculumCourseResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    curriculum_id = fields.UUID(dump_only=True)
    course_id = fields.UUID(dump_only=True)
    semester_id = fields.UUID(dump_only=True)
    sequence_order = fields.Integer(dump_only=True)
    credits_override = fields.Integer(allow_none=True, dump_only=True)
    required_hours = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )
    course_code = fields.Method("get_course_code", dump_only=True)
    course_name = fields.Method("get_course_name", dump_only=True)
    semester_number = fields.Method("get_semester_number", dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @staticmethod
    def get_course_code(obj):
        return obj.course.course_code

    @staticmethod
    def get_course_name(obj):
        return obj.course.course_name

    @staticmethod
    def get_semester_number(obj):
        return obj.semester.semester_number


class SyllabusCreateSchema(NonBlankSchema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=150))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    objectives = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    version = fields.Integer(validate=validate.Range(min=1))


class SyllabusUpdateSchema(NonBlankSchema):
    title = fields.String(validate=validate.Length(min=1, max=150))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    objectives = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided.")


class SyllabusResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    curriculum_course_id = fields.UUID(dump_only=True)
    title = fields.String(dump_only=True)
    description = fields.String(allow_none=True, dump_only=True)
    objectives = fields.String(allow_none=True, dump_only=True)
    version = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class SyllabusUnitCreateSchema(NonBlankSchema):
    unit_number = fields.Integer(required=True, validate=validate.Range(min=1))
    title = fields.String(required=True, validate=validate.Length(min=1, max=150))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    sequence_order = fields.Integer(required=True, validate=validate.Range(min=1))
    teaching_hours = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )


class SyllabusUnitUpdateSchema(NonBlankSchema):
    unit_number = fields.Integer(validate=validate.Range(min=1))
    title = fields.String(validate=validate.Length(min=1, max=150))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    sequence_order = fields.Integer(validate=validate.Range(min=1))
    teaching_hours = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided.")


class SyllabusUnitResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    syllabus_id = fields.UUID(dump_only=True)
    unit_number = fields.Integer(dump_only=True)
    title = fields.String(dump_only=True)
    description = fields.String(allow_none=True, dump_only=True)
    sequence_order = fields.Integer(dump_only=True)
    teaching_hours = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class SyllabusTopicCreateSchema(NonBlankSchema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    sequence_order = fields.Integer(required=True, validate=validate.Range(min=1))
    teaching_hours = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )
    reference_url = fields.String(allow_none=True, validate=validate.Length(max=2048))


class SyllabusTopicUpdateSchema(NonBlankSchema):
    title = fields.String(validate=validate.Length(min=1, max=200))
    description = fields.String(allow_none=True, validate=validate.Length(max=MAX_TEXT_LENGTH))
    sequence_order = fields.Integer(validate=validate.Range(min=1))
    teaching_hours = fields.Decimal(
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )
    reference_url = fields.String(allow_none=True, validate=validate.Length(max=2048))

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided.")


class SyllabusTopicResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    unit_id = fields.UUID(dump_only=True)
    title = fields.String(dump_only=True)
    description = fields.String(allow_none=True, dump_only=True)
    sequence_order = fields.Integer(dump_only=True)
    teaching_hours = fields.Decimal(
        as_string=True,
        allow_none=True,
        dump_only=True,
    )
    reference_url = fields.String(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class LearningOutcomeCreateSchema(NonBlankSchema):
    outcome_code = fields.String(required=True, validate=validate.Length(min=1, max=30))
    description = fields.String(required=True, validate=validate.Length(min=1, max=MAX_TEXT_LENGTH))
    outcome_type = fields.String(allow_none=True, validate=validate.Length(max=50))


class LearningOutcomeUpdateSchema(NonBlankSchema):
    outcome_code = fields.String(validate=validate.Length(min=1, max=30))
    description = fields.String(validate=validate.Length(min=1, max=MAX_TEXT_LENGTH))
    outcome_type = fields.String(allow_none=True, validate=validate.Length(max=50))

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError("At least one field must be provided.")


class LearningOutcomeResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    syllabus_id = fields.UUID(dump_only=True)
    outcome_code = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    outcome_type = fields.String(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class TopicLearningOutcomeCreateSchema(Schema):
    learning_outcome_id = fields.UUID(required=True)


class TopicLearningOutcomeResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    topic_id = fields.UUID(dump_only=True)
    learning_outcome_id = fields.UUID(dump_only=True)
    outcome_code = fields.Method("get_outcome_code", dump_only=True)
    description = fields.Method("get_description", dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @staticmethod
    def get_outcome_code(obj):
        return obj.learning_outcome.outcome_code

    @staticmethod
    def get_description(obj):
        return obj.learning_outcome.description
