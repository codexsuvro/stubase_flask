from marshmallow import Schema, fields, validate


class DepartmentCreateSchema(Schema):
    department_code = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
        metadata={"example": "CSE"},
    )

    department_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        metadata={"example": "Computer Science and Engineering"},
    )

    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
        metadata={"example": "cse@stubase.com"},
    )

    phone = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
        metadata={"example": "9876543210"},
    )


class DepartmentResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    department_code = fields.String(dump_only=True)
    department_name = fields.String(dump_only=True)
    hod_faculty_id = fields.UUID(allow_none=True, dump_only=True)
    email = fields.Email(dump_only=True)
    phone = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class DepartmentHODAssignSchema(Schema):
    faculty_user_id = fields.UUID(
        required=True,
        metadata={
            "description": "UUID of the User account belonging to the Faculty."
        },
    )
