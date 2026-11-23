from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates,
    validates_schema,
)


ANNOUNCEMENT_AUDIENCES = ("GLOBAL", "COURSE")
ANNOUNCEMENT_STATUSES = ("DRAFT", "PUBLISHED", "ARCHIVED")


class AnnouncementCreateSchema(Schema):
    audience_type = fields.String(
        required=True,
        validate=validate.OneOf(ANNOUNCEMENT_AUDIENCES),
    )
    offering_id = fields.UUID(allow_none=True)
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=200),
    )
    body = fields.String(
        required=True,
        validate=validate.Length(min=1, max=10000),
    )

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value.strip() or "\r" in value or "\n" in value:
            raise ValidationError(
                "Title must be a non-empty single line."
            )

    @validates("body")
    def validate_body(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Body cannot contain only whitespace.")

    @validates_schema
    def validate_audience(self, data, **kwargs):
        audience_type = data.get("audience_type")
        offering_id = data.get("offering_id")

        if audience_type == "GLOBAL" and offering_id is not None:
            raise ValidationError(
                {"offering_id": ["Global announcements cannot target an offering."]}
            )

        if audience_type == "COURSE" and offering_id is None:
            raise ValidationError(
                {"offering_id": ["Course announcements require an offering."]}
            )


class AnnouncementUpdateSchema(Schema):
    title = fields.String(
        validate=validate.Length(min=1, max=200),
    )
    body = fields.String(
        validate=validate.Length(min=1, max=10000),
    )

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value.strip() or "\r" in value or "\n" in value:
            raise ValidationError(
                "Title must be a non-empty single line."
            )

    @validates("body")
    def validate_body(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Body cannot contain only whitespace.")

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field must be provided for an update."
            )


class AnnouncementQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    status = fields.String(
        validate=validate.OneOf(ANNOUNCEMENT_STATUSES),
    )


class AnnouncementResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    audience_type = fields.String(dump_only=True)
    offering_id = fields.UUID(allow_none=True, dump_only=True)
    created_by = fields.UUID(dump_only=True)
    title = fields.String(dump_only=True)
    body = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    published_at = fields.DateTime(allow_none=True, dump_only=True)
    archived_at = fields.DateTime(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AnnouncementPaginationSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class AnnouncementPaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(AnnouncementResponseSchema),
        dump_only=True,
    )
    pagination = fields.Nested(
        AnnouncementPaginationSchema,
        dump_only=True,
    )
