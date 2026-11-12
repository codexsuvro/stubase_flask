from marshmallow import Schema, fields, validate


class CoursePrerequisiteCreateSchema(Schema):

    prerequisite_course_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the course that must be completed first."
        },
    )


class CoursePrerequisiteResponseSchema(Schema):

    id = fields.UUID(dump_only=True)
    course_id = fields.UUID(dump_only=True)
    prerequisite_course_id = fields.UUID(dump_only=True)
    course = fields.Method("get_course", dump_only=True)

    prerequisite_course = fields.Method(
        "get_prerequisite_course",
        dump_only=True,
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_course(self, obj):
        return {
            "id": str(obj.course.id),
            "course_code": obj.course.course_code,
            "course_name": obj.course.course_name,
        }

    def get_prerequisite_course(self, obj):
        return {
            "id": str(obj.prerequisite_course.id),
            "course_code": obj.prerequisite_course.course_code,
            "course_name": obj.prerequisite_course.course_name,
        }