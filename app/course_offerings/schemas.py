from marshmallow import Schema, fields, validate


class CourseOfferingCreateSchema(Schema):
    course_id = fields.UUID(required=True)
    semester_id = fields.UUID(required=True)
    faculty_id = fields.UUID(required=True)
    section_code = fields.String(required=True, validate=validate.Length(min=1, max=10))
    capacity = fields.Integer(required=True, validate=validate.Range(min=1, max=10000))
    status = fields.String(load_default="DRAFT", validate=validate.OneOf(["DRAFT", "OPEN", "CLOSED", "CANCELLED"]))


class CourseOfferingUpdateSchema(Schema):
    faculty_id = fields.UUID()
    section_code = fields.String(validate=validate.Length(min=1, max=10))
    capacity = fields.Integer(validate=validate.Range(min=1, max=10000))


class CourseOfferingStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(["DRAFT", "OPEN", "CLOSED", "CANCELLED"]))


class CourseOfferingResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    course_id = fields.UUID(dump_only=True)
    semester_id = fields.UUID(dump_only=True)
    faculty_id = fields.UUID(dump_only=True)
    section_code = fields.String(dump_only=True)
    capacity = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
    course = fields.Method("get_course", dump_only=True)
    semester = fields.Method("get_semester", dump_only=True)
    faculty = fields.Method("get_faculty", dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_course(self, obj):
        return {"id": str(obj.course.id), "course_code": obj.course.course_code,
                "course_name": obj.course.course_name, "credits": obj.course.credits}

    def get_semester(self, obj):
        return {"id": str(obj.semester.id), "semester_number": obj.semester.semester_number,
                "semester_name": obj.semester.semester_name,
                "academic_year": obj.semester.academic_year.name}

    def get_faculty(self, obj):
        return {"id": str(obj.faculty.id), "faculty_id": obj.faculty.faculty_id,
                "first_name": obj.faculty.first_name, "last_name": obj.faculty.last_name,
                "email": obj.faculty.email}
