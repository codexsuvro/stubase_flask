
from flask import send_file
from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from flask_smorest import Blueprint, abort
from sqlalchemy import select

from app.extensions import db
from app.auth.permissions import role_required
from app.auth.repository import get_user_by_id
from app.models.student import Student

from app.grading.schemas import (
    GradingSchemeCreateSchema,
    GradingSchemeUpdateSchema,
    GradingSchemeResponseSchema,
    CourseGradeCalculateSchema,
    CourseGradeResponseSchema,
    TranscriptResponseSchema,
    SemesterTranscriptQuerySchema,
    YearTranscriptQuerySchema,
    SemesterTranscriptResponseSchema,
    YearTranscriptResponseSchema,
)

from app.grading import service
from app.grading.pdf import generate_transcript_pdf


blp = Blueprint(
    "grading",
    __name__,
    url_prefix="/grading",
    description="Grading and Academic Performance",
)


def get_current_user():
    user = get_user_by_id(get_jwt_identity())

    if not user:
        abort(401, message="Authenticated user not found.")

    return user



def create_transcript_pdf_response(
    transcript,
    filename,
    title="ACADEMIC TRANSCRIPT",
    metric_label="CGPA",
    metric_value=None,
    period_label=None,
):
    pdf_buffer = generate_transcript_pdf(
        transcript,
        title=title,
        metric_label=metric_label,
        metric_value=metric_value,
        period_label=period_label,
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@blp.route("/schemes")
class GradingSchemeListResource(MethodView):

    @blp.arguments(GradingSchemeCreateSchema)
    @blp.response(201, GradingSchemeResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return service.create_grading_scheme(data)

        except service.GradingError as exc:
            abort(400, message=str(exc))

    @blp.response(200, GradingSchemeResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY")
    def get(self):
        return service.list_grading_schemes()


@blp.route("/schemes/<uuid:scheme_id>")
class GradingSchemeDetailResource(MethodView):

    @blp.arguments(GradingSchemeUpdateSchema)
    @blp.response(200, GradingSchemeResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, scheme_id):
        try:
            return service.update_grading_scheme(
                scheme_id,
                data,
            )

        except service.GradingNotFoundError as exc:
            abort(404, message=str(exc))

        except service.GradingError as exc:
            abort(400, message=str(exc))


@blp.route("/course-grades/calculate")
class CourseGradeCalculateResource(MethodView):

    @blp.arguments(CourseGradeCalculateSchema)
    @blp.response(200, CourseGradeResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, data):
        user = get_current_user()

        try:
            return service.calculate_course_grade(
                data["enrollment_id"],
                data["grading_scheme_id"],
                user=user,
            )

        except service.GradingNotFoundError as exc:
            abort(404, message=str(exc))

        except service.GradingAccessDeniedError as exc:
            abort(403, message=str(exc))

        except service.GradingError as exc:
            abort(400, message=str(exc))


@blp.route("/course-grades/<uuid:grade_id>/publish")
class CourseGradePublishResource(MethodView):

    @blp.response(200, CourseGradeResponseSchema)
    @role_required("ADMIN")
    def post(self, grade_id):
        try:
            return service.publish_course_grade(
                grade_id,
                get_jwt_identity(),
            )

        except service.GradingNotFoundError as exc:
            abort(404, message=str(exc))

        except service.GradingError as exc:
            abort(400, message=str(exc))


@blp.route("/transcripts/me")
class MyTranscriptResource(MethodView):

    @blp.response(200, TranscriptResponseSchema)
    @role_required("STUDENT")
    def get(self):
        user = get_current_user()

        if not user.student:
            abort(404, message="Student profile not found.")

        return service.get_student_transcript(user.student)


@blp.route("/transcripts/<uuid:student_id>")
class StudentTranscriptResource(MethodView):

    @blp.response(200, TranscriptResponseSchema)
    @role_required("ADMIN")
    def get(self, student_id):
        student = db.session.scalar(
            select(Student).where(Student.id == student_id)
        )

        if not student:
            abort(404, message="Student not found.")

        return service.get_student_transcript(student)


# ==================================================
# Transcript PDF Download
# ==================================================

@blp.route("/transcripts/me/pdf")
class MyTranscriptPDFResource(MethodView):

    @role_required("STUDENT")
    def get(self):
        user = get_current_user()

        if not user.student:
            abort(404, message="Student profile not found.")

        student = user.student

        transcript = service.get_student_transcript(student)

        filename = f"transcript_{student.student_id}.pdf"

        return create_transcript_pdf_response(
            transcript,
            filename,
        )


@blp.route("/transcripts/<uuid:student_id>/pdf")
class StudentTranscriptPDFResource(MethodView):

    @role_required("ADMIN")
    def get(self, student_id):
        student = db.session.scalar(
            select(Student).where(Student.id == student_id)
        )

        if not student:
            abort(404, message="Student not found.")

        transcript = service.get_student_transcript(student)

        filename = f"transcript_{student.student_id}.pdf"

        return create_transcript_pdf_response(
            transcript,
            filename,
        )

# ==================================================
# Semester-wise Transcript APIs
# ==================================================

@blp.route("/transcripts/me/semester")
class MySemesterTranscriptResource(MethodView):

    @blp.arguments(
        SemesterTranscriptQuerySchema,
        location="query",
    )
    @blp.response(200, SemesterTranscriptResponseSchema)
    @role_required("STUDENT")
    def get(self, query_data):
        user = get_current_user()

        if not user.student:
            abort(404, message="Student profile not found.")

        transcript = service.get_semester_transcript(
            user.student,
            query_data["academic_year"],
            query_data["semester"],
        )

        return {
            **transcript,
            "sgpa": transcript["gpa"],
        }


@blp.route("/transcripts/<uuid:student_id>/semester")
class StudentSemesterTranscriptResource(MethodView):

    @blp.arguments(
        SemesterTranscriptQuerySchema,
        location="query",
    )
    @blp.response(200, SemesterTranscriptResponseSchema)
    @role_required("ADMIN")
    def get(self, query_data, student_id):
        student = db.session.scalar(
            select(Student).where(Student.id == student_id)
        )

        if not student:
            abort(404, message="Student not found.")

        transcript = service.get_semester_transcript(
            student,
            query_data["academic_year"],
            query_data["semester"],
        )

        return {
            **transcript,
            "sgpa": transcript["gpa"],
        }


# ==================================================
# Year-wise Transcript APIs
# ==================================================

@blp.route("/transcripts/me/year")
class MyYearTranscriptResource(MethodView):

    @blp.arguments(
        YearTranscriptQuerySchema,
        location="query",
    )
    @blp.response(200, YearTranscriptResponseSchema)
    @role_required("STUDENT")
    def get(self, query_data):
        user = get_current_user()

        if not user.student:
            abort(404, message="Student profile not found.")

        transcript = service.get_year_transcript(
            user.student,
            query_data["academic_year"],
        )

        return {
            **transcript,
            "year_gpa": transcript["gpa"],
        }


@blp.route("/transcripts/<uuid:student_id>/year")
class StudentYearTranscriptResource(MethodView):

    @blp.arguments(
        YearTranscriptQuerySchema,
        location="query",
    )
    @blp.response(200, YearTranscriptResponseSchema)
    @role_required("ADMIN")
    def get(self, query_data, student_id):
        student = db.session.scalar(
            select(Student).where(Student.id == student_id)
        )

        if not student:
            abort(404, message="Student not found.")

        transcript = service.get_year_transcript(
            student,
            query_data["academic_year"],
        )

        return {
            **transcript,
            "year_gpa": transcript["gpa"],
        }


# ==================================================
# Semester-wise Transcript PDF
# ==================================================

@blp.route("/transcripts/me/semester/pdf")
class MySemesterTranscriptPDFResource(MethodView):

    @blp.arguments(
        SemesterTranscriptQuerySchema,
        location="query",
    )
    @role_required("STUDENT")
    def get(self, query_data):
        user = get_current_user()

        if not user.student:
            abort(404, message="Student profile not found.")

        student = user.student

        transcript = service.get_semester_transcript(
            student,
            query_data["academic_year"],
            query_data["semester"],
        )

        return create_transcript_pdf_response(
            transcript,
            f"transcript_{student.student_id}_"
            f"{query_data['academic_year']}_"
            f"semester_{query_data['semester']}.pdf",
            title="SEMESTER-WISE ACADEMIC TRANSCRIPT",
            metric_label="SGPA",
            metric_value=transcript["gpa"],
            period_label=(
                f"Academic Year: {query_data['academic_year']} | "
                f"Semester: {query_data['semester']}"
            ),
        )


@blp.route("/transcripts/<uuid:student_id>/semester/pdf")
class StudentSemesterTranscriptPDFResource(MethodView):

    @blp.arguments(
        SemesterTranscriptQuerySchema,
        location="query",
    )
    @role_required("ADMIN")
    def get(self, query_data, student_id):
        student = db.session.scalar(
            select(Student).where(Student.id == student_id)
        )

        if not student:
            abort(404, message="Student not found.")

        transcript = service.get_semester_transcript(
            student,
            query_data["academic_year"],
            query_data["semester"],
        )

        return create_transcript_pdf_response(
            transcript,
            f"transcript_{student.student_id}_"
            f"{query_data['academic_year']}_"
            f"semester_{query_data['semester']}.pdf",
            title="SEMESTER-WISE ACADEMIC TRANSCRIPT",
            metric_label="SGPA",
            metric_value=transcript["gpa"],
            period_label=(
                f"Academic Year: {query_data['academic_year']} | "
                f"Semester: {query_data['semester']}"
            ),
        )


# ==================================================
# Year-wise Transcript PDF
# ==================================================

@blp.route("/transcripts/me/year/pdf")
class MyYearTranscriptPDFResource(MethodView):

    @blp.arguments(
        YearTranscriptQuerySchema,
        location="query",
    )
    @role_required("STUDENT")
    def get(self, query_data):
        user = get_current_user()

        if not user.student:
            abort(404, message="Student profile not found.")

        student = user.student

        transcript = service.get_year_transcript(
            student,
            query_data["academic_year"],
        )

        return create_transcript_pdf_response(
            transcript,
            f"transcript_{student.student_id}_"
            f"{query_data['academic_year']}_year.pdf",
            title="ACADEMIC YEAR TRANSCRIPT",
            metric_label="YEAR GPA",
            metric_value=transcript["gpa"],
            period_label=(
                f"Academic Year: {query_data['academic_year']}"
            ),
        )


@blp.route("/transcripts/<uuid:student_id>/year/pdf")
class StudentYearTranscriptPDFResource(MethodView):

    @blp.arguments(
        YearTranscriptQuerySchema,
        location="query",
    )
    @role_required("ADMIN")
    def get(self, query_data, student_id):
        student = db.session.scalar(
            select(Student).where(Student.id == student_id)
        )

        if not student:
            abort(404, message="Student not found.")

        transcript = service.get_year_transcript(
            student,
            query_data["academic_year"],
        )

        return create_transcript_pdf_response(
            transcript,
            f"transcript_{student.student_id}_"
            f"{query_data['academic_year']}_year.pdf",
            title="ACADEMIC YEAR TRANSCRIPT",
            metric_label="YEAR GPA",
            metric_value=transcript["gpa"],
            period_label=(
                f"Academic Year: {query_data['academic_year']}"
            ),
        )
