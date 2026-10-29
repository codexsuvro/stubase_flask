from marshmallow import Schema, fields, validate


class CourseCreateSchema(Schema):
    course_code = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
        metadata={"example": "CS301"},
    )

    course_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"example": "Database Management Systems"},
    )

    credits = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=10),
        metadata={"example": 4},
    )

    semester = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=12),
        metadata={"example": 3},
    )

    department_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the Department offering this course."
        },
    )

    faculty_user_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the User account belonging to the assigned Faculty."
        },
    )


class CourseDepartmentSummarySchema(Schema):
    id = fields.UUID(dump_only=True)
    department_code = fields.String(dump_only=True)
    department_name = fields.String(dump_only=True)


class CourseFacultySummarySchema(Schema):
    id = fields.UUID(dump_only=True)
    faculty_id = fields.String(dump_only=True)
    first_name = fields.String(dump_only=True)
    last_name = fields.String(dump_only=True)
    designation = fields.String(dump_only=True)
    email = fields.Email(dump_only=True)


class CourseResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    course_code = fields.String(dump_only=True)
    course_name = fields.String(dump_only=True)
    credits = fields.Integer(dump_only=True)
    semester = fields.Integer(dump_only=True)

    department_id = fields.UUID(dump_only=True)
    faculty_id = fields.UUID(dump_only=True)

    department = fields.Nested(
        CourseDepartmentSummarySchema,
        dump_only=True,
    )

    faculty = fields.Nested(
        CourseFacultySummarySchema,
        dump_only=True,
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
