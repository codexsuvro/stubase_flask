
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
)

from app.grading import service


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
