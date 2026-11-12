from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.course_prerequisites.schemas import (
    CoursePrerequisiteCreateSchema,
    CoursePrerequisiteResponseSchema,
)
from app.course_prerequisites.service import (
    create_prerequisite,
    get_course_prerequisites,
    remove_prerequisite,
    CoursePrerequisiteNotFoundError,
    CoursePrerequisiteConflictError,
    InvalidCoursePrerequisiteError,
)


blp = Blueprint(
    "Course Prerequisites",
    __name__,
    url_prefix="/courses",
    description="Course prerequisite management.",
)


def handle_error(exc):

    if isinstance(exc, CoursePrerequisiteNotFoundError):
        abort(404, message=str(exc))

    if isinstance(exc, CoursePrerequisiteConflictError):
        abort(409, message=str(exc))

    if isinstance(exc, InvalidCoursePrerequisiteError):
        abort(422, message=str(exc))

    raise exc


@blp.route("/<uuid:course_id>/prerequisites")
class CoursePrerequisiteCollectionResource(MethodView):

    @blp.doc(
        summary="Configure a course prerequisite",
        description="ADMIN only. Adds a prerequisite to a course.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(CoursePrerequisiteCreateSchema)
    @blp.response(201, CoursePrerequisiteResponseSchema)
    @role_required("ADMIN")
    def post(self, data, course_id):

        try:
            return create_prerequisite(
                course_id,
                data["prerequisite_course_id"],
            )

        except Exception as exc:
            handle_error(exc)

    @blp.doc(
        summary="List course prerequisites",
        description="ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(
        200,
        CoursePrerequisiteResponseSchema(many=True),
    )
    @role_required("ADMIN")
    def get(self, course_id):

        try:
            return get_course_prerequisites(course_id)

        except Exception as exc:
            handle_error(exc)


@blp.route(
    "/<uuid:course_id>/prerequisites/<uuid:prerequisite_course_id>"
)
class CoursePrerequisiteDetailResource(MethodView):

    @blp.doc(
        summary="Remove a course prerequisite",
        description="ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200)
    @role_required("ADMIN")
    def delete(self, course_id, prerequisite_course_id):

        try:
            return remove_prerequisite(
                course_id,
                prerequisite_course_id,
            )

        except Exception as exc:
            handle_error(exc)