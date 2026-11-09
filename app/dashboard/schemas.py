
from marshmallow import Schema, fields


class DashboardMetricsSchema(Schema):
    total_students = fields.Integer()
    total_faculty = fields.Integer()
    total_departments = fields.Integer()
    total_courses = fields.Integer()
    assigned_courses = fields.Integer()
    active_enrollments = fields.Integer()
    total_attendance_records = fields.Integer()
    overall_attendance_percentage = fields.Float()
    total_assessment_results = fields.Integer()
    overall_result_percentage = fields.Float()


class DashboardAssessmentSchema(Schema):
    id = fields.UUID()
    assessment_name = fields.String()
    assessment_type = fields.String()
    sequence_number = fields.Integer()
    semester = fields.Integer()
    academic_year = fields.String()
    max_marks = fields.Decimal(as_string=True, places=2)
    passing_marks = fields.Decimal(as_string=True, places=2)
    assessment_date = fields.Date()


class StudentDashboardSchema(DashboardMetricsSchema):
    upcoming_assessments = fields.List(
        fields.Nested(DashboardAssessmentSchema)
    )
