from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


STATUS_VALUES = ["PLANNED", "ACTIVE", "COMPLETED"]


class AcademicYearCreateSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=4, max=20),
        metadata={"example": "2026-2027"},
    )

    start_date = fields.Date(
        required=True,
        metadata={"example": "2026-07-01"},
    )

    end_date = fields.Date(
        required=True,
        metadata={"example": "2027-06-30"},
    )

    status = fields.String(
        load_default="PLANNED",
        validate=validate.OneOf(STATUS_VALUES),
    )

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if (
            data.get("start_date")
            and data.get("end_date")
            and data["start_date"] >= data["end_date"]
        ):
            raise ValidationError({
                "end_date": ["End date must be after start date."]
            })


class AcademicYearUpdateSchema(Schema):
    name = fields.String(
        validate=validate.Length(min=4, max=20),
    )

    start_date = fields.Date()
    end_date = fields.Date()

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if (
            data.get("start_date")
            and data.get("end_date")
            and data["start_date"] >= data["end_date"]
        ):
            raise ValidationError({
                "end_date": ["End date must be after start date."]
            })

        if not data:
            raise ValidationError("At least one field is required.")


class AcademicYearStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(STATUS_VALUES),
    )


class AcademicYearResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.String(dump_only=True)
    start_date = fields.Date(dump_only=True)
    end_date = fields.Date(dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class SemesterCreateSchema(Schema):
    academic_year_id = fields.UUID(required=True)

    semester_number = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=8),
    )

    semester_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=50),
        metadata={"example": "Odd Semester"},
    )

    start_date = fields.Date(
        required=True,
        metadata={"example": "2026-07-01"},
    )

    end_date = fields.Date(
        required=True,
        metadata={"example": "2026-12-15"},
    )

    status = fields.String(
        load_default="PLANNED",
        validate=validate.OneOf(STATUS_VALUES),
    )

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if (
            data.get("start_date")
            and data.get("end_date")
            and data["start_date"] >= data["end_date"]
        ):
            raise ValidationError({
                "end_date": ["End date must be after start date."]
            })


class SemesterUpdateSchema(Schema):
    semester_number = fields.Integer(
        validate=validate.Range(min=1, max=8),
    )

    semester_name = fields.String(
        validate=validate.Length(min=2, max=50),
    )

    start_date = fields.Date()
    end_date = fields.Date()

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if (
            data.get("start_date")
            and data.get("end_date")
            and data["start_date"] >= data["end_date"]
        ):
            raise ValidationError({
                "end_date": ["End date must be after start date."]
            })

        if not data:
            raise ValidationError("At least one field is required.")


class SemesterStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(STATUS_VALUES),
    )


class SemesterResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    academic_year_id = fields.UUID(dump_only=True)
    academic_year_name = fields.Method("get_academic_year_name")
    semester_number = fields.Integer(dump_only=True)
    semester_name = fields.String(dump_only=True)
    start_date = fields.Date(dump_only=True)
    end_date = fields.Date(dump_only=True)
    status = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @staticmethod
    def get_academic_year_name(obj):
        return obj.academic_year.name if obj.academic_year else None
    
    
class SemesterFilterSchema(Schema):
    academic_year_id = fields.UUID(required=False)

    status = fields.String(
        required=False,
        validate=validate.OneOf(STATUS_VALUES),
    )