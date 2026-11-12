from marshmallow import Schema, fields, validate


class WaitlistJoinSchema(Schema):

    offering_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the full course offering."
        },
    )


class WaitlistResponseSchema(Schema):

    id = fields.UUID(dump_only=True)
    student_id = fields.UUID(dump_only=True)
    offering_id = fields.UUID(dump_only=True)

    status = fields.String(
        dump_only=True,
        validate=validate.OneOf(
            ["WAITING", "PROMOTED", "CANCELLED", "INELIGIBLE"]
        ),
    )

    promoted_enrollment_id = fields.UUID(
        dump_only=True,
        allow_none=True,
    )

    student = fields.Method(
        "get_student",
        dump_only=True,
    )

    offering = fields.Method(
        "get_offering",
        dump_only=True,
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_student(self, obj):

        return {
            "id": str(obj.student.id),
            "student_id": obj.student.student_id,
            "first_name": obj.student.first_name,
            "last_name": obj.student.last_name,
        }

    def get_offering(self, obj):

        return {
            "id": str(obj.offering.id),
            "section_code": obj.offering.section_code,
            "status": obj.offering.status,
            "capacity": obj.offering.capacity,
            "course_code": obj.offering.course.course_code,
            "course_name": obj.offering.course.course_name,
        }


class WaitlistPromotionResponseSchema(Schema):

    message = fields.String(dump_only=True)
    waitlist_id = fields.UUID(dump_only=True)
    enrollment_id = fields.UUID(dump_only=True)
    student_id = fields.UUID(dump_only=True)
    offering_id = fields.UUID(dump_only=True)