from marshmallow import Schema, fields, validate


class NotificationQuerySchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )
    per_page = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    unread_only = fields.Boolean(load_default=False)


class NotificationResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    notification_type = fields.String(dump_only=True)
    title = fields.String(dump_only=True)
    message = fields.String(dump_only=True)
    announcement_id = fields.UUID(allow_none=True, dump_only=True)
    read_at = fields.DateTime(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class NotificationPaginationSchema(Schema):
    page = fields.Integer(dump_only=True)
    per_page = fields.Integer(dump_only=True)
    total_records = fields.Integer(dump_only=True)
    total_pages = fields.Integer(dump_only=True)
    has_next = fields.Boolean(dump_only=True)
    has_previous = fields.Boolean(dump_only=True)


class NotificationPaginatedResponseSchema(Schema):
    items = fields.List(
        fields.Nested(NotificationResponseSchema),
        dump_only=True,
    )
    pagination = fields.Nested(
        NotificationPaginationSchema,
        dump_only=True,
    )


class UnreadNotificationCountSchema(Schema):
    unread_count = fields.Integer(dump_only=True)


class MarkAllNotificationsReadSchema(Schema):
    updated_count = fields.Integer(dump_only=True)
