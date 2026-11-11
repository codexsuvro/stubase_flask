from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


ROOM_TYPES = [
    "CLASSROOM",
    "LABORATORY",
    "LECTURE_HALL",
    "SEMINAR_HALL",
]

ROOM_STATUSES = ["ACTIVE", "INACTIVE"]

SESSION_TYPES = [
    "LECTURE",
    "PRACTICAL",
    "TUTORIAL",
    "SEMINAR",
]

SLOT_STATUSES = ["ACTIVE", "CANCELLED"]


class ClassroomCreateSchema(Schema):

    building = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )

    room_number = fields.String(
        required=True,
        validate=validate.Length(min=1, max=30),
    )

    capacity = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    room_type = fields.String(
        load_default="CLASSROOM",
        validate=validate.OneOf(ROOM_TYPES),
    )


class ClassroomUpdateSchema(Schema):

    building = fields.String(
        validate=validate.Length(min=1, max=100),
    )

    room_number = fields.String(
        validate=validate.Length(min=1, max=30),
    )

    capacity = fields.Integer(
        validate=validate.Range(min=1),
    )

    room_type = fields.String(
        validate=validate.OneOf(ROOM_TYPES),
    )

    status = fields.String(
        validate=validate.OneOf(ROOM_STATUSES),
    )

    @validates_schema
    def validate_payload(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one field is required."
            )


class ClassroomResponseSchema(Schema):

    id = fields.UUID(dump_only=True)
    building = fields.String(dump_only=True)
    room_number = fields.String(dump_only=True)
    capacity = fields.Integer(dump_only=True)
    room_type = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class TimetableSlotCreateSchema(Schema):

    offering_id = fields.UUID(required=True)
    classroom_id = fields.UUID(required=True)

    day_of_week = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=7),
    )

    start_time = fields.Time(required=True)
    end_time = fields.Time(required=True)

    effective_from = fields.Date(required=True)
    effective_until = fields.Date(required=True)

    session_type = fields.String(
        load_default="LECTURE",
        validate=validate.OneOf(SESSION_TYPES),
    )

    remarks = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
    )

    @validates_schema
    def validate_slot(self, data, **kwargs):

        if (
            data.get("start_time")
            and data.get("end_time")
            and data["start_time"] >= data["end_time"]
        ):
            raise ValidationError({
                "end_time": [
                    "End time must be after start time."
                ]
            })

        if (
            data.get("effective_from")
            and data.get("effective_until")
            and data["effective_from"] > data["effective_until"]
        ):
            raise ValidationError({
                "effective_until": [
                    "Effective until must be on or after effective from."
                ]
            })


class TimetableSlotUpdateSchema(Schema):

    classroom_id = fields.UUID()

    day_of_week = fields.Integer(
        validate=validate.Range(min=1, max=7),
    )

    start_time = fields.Time()
    end_time = fields.Time()

    effective_from = fields.Date()
    effective_until = fields.Date()

    session_type = fields.String(
        validate=validate.OneOf(SESSION_TYPES),
    )

    status = fields.String(
        validate=validate.OneOf(SLOT_STATUSES),
    )

    remarks = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
    )

    @validates_schema
    def validate_slot(self, data, **kwargs):

        if (
            data.get("start_time")
            and data.get("end_time")
            and data["start_time"] >= data["end_time"]
        ):
            raise ValidationError({
                "end_time": [
                    "End time must be after start time."
                ]
            })

        if (
            data.get("effective_from")
            and data.get("effective_until")
            and data["effective_from"] > data["effective_until"]
        ):
            raise ValidationError({
                "effective_until": [
                    "Effective until must be on or after effective from."
                ]
            })

        if not data:
            raise ValidationError(
                "At least one field is required."
            )


class TimetableSlotFilterSchema(Schema):

    offering_id = fields.UUID()
    faculty_id = fields.UUID()
    classroom_id = fields.UUID()
    semester_id = fields.UUID()

    day_of_week = fields.Integer(
        validate=validate.Range(min=1, max=7),
    )

    status = fields.String(
        load_default="ACTIVE",
        validate=validate.OneOf(SLOT_STATUSES),
    )


class TimetableSlotResponseSchema(Schema):

    id = fields.UUID(dump_only=True)

    offering_id = fields.UUID(dump_only=True)
    faculty_id = fields.UUID(dump_only=True)
    classroom_id = fields.UUID(dump_only=True)

    day_of_week = fields.Integer(dump_only=True)
    start_time = fields.Time(dump_only=True)
    end_time = fields.Time(dump_only=True)

    effective_from = fields.Date(dump_only=True)
    effective_until = fields.Date(dump_only=True)

    session_type = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    remarks = fields.String(dump_only=True)

    course_code = fields.Method("get_course_code")
    course_name = fields.Method("get_course_name")
    section_code = fields.Method("get_section_code")
    faculty_name = fields.Method("get_faculty_name")
    classroom_name = fields.Method("get_classroom_name")

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @staticmethod
    def get_course_code(obj):
        return obj.offering.course.course_code

    @staticmethod
    def get_course_name(obj):
        return obj.offering.course.course_name

    @staticmethod
    def get_section_code(obj):
        return obj.offering.section_code

    @staticmethod
    def get_faculty_name(obj):
        return (
            f"{obj.faculty.first_name} "
            f"{obj.faculty.last_name}"
        )

    @staticmethod
    def get_classroom_name(obj):
        return (
            f"{obj.classroom.building} - "
            f"{obj.classroom.room_number}"
        )
