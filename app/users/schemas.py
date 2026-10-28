from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates_schema,
)


class FacultyProfileCreateSchema(Schema):
    faculty_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
    )
    first_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
    )
    last_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
    )
    designation = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
    )
    phone = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
    )
    department_id = fields.UUID(required=True)


class StudentProfileCreateSchema(Schema):
    student_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
    )
    first_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
    )
    last_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
    )
    gender = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
    )
    date_of_birth = fields.Date(required=True)
    phone = fields.String(
        required=True,
        validate=validate.Length(min=1, max=15),
    )
    admission_date = fields.Date(required=True)
    department_id = fields.UUID(required=True)


class UserCreateSchema(Schema):
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=50),
        metadata={"example": "testfaculty"},
    )
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
        metadata={"example": "faculty@stubase.com"},
    )
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(
            min=12,
            max=128,
            error="Password must be between 12 and 128 characters.",
        ),
    )
    role = fields.String(
        required=True,
        validate=validate.OneOf(["FACULTY", "STUDENT"]),
    )
    faculty_profile = fields.Nested(
        FacultyProfileCreateSchema,
        required=False,
    )
    student_profile = fields.Nested(
        StudentProfileCreateSchema,
        required=False,
    )

    @validates_schema
    def validate_profile_for_role(self, data, **kwargs):
        role = data.get("role")
        faculty_profile = data.get("faculty_profile")
        student_profile = data.get("student_profile")

        if role == "FACULTY":
            if not faculty_profile:
                raise ValidationError({
                    "faculty_profile": [
                        "This field is required when role is FACULTY."
                    ]
                })
            if student_profile:
                raise ValidationError({
                    "student_profile": [
                        "Do not provide student_profile for a FACULTY account."
                    ]
                })

        elif role == "STUDENT":
            if not student_profile:
                raise ValidationError({
                    "student_profile": [
                        "This field is required when role is STUDENT."
                    ]
                })
            if faculty_profile:
                raise ValidationError({
                    "faculty_profile": [
                        "Do not provide faculty_profile for a STUDENT account."
                    ]
                })


class UserResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    username = fields.String(dump_only=True)
    email = fields.Email(dump_only=True)
    role = fields.Method("get_role", dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    is_verified = fields.Boolean(dump_only=True)

    @staticmethod
    def get_role(obj):
        return obj.role.role_name if obj.role else None
