from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity
from app.auth.permissions import role_required
from app.auth.repository import get_user_by_id
from app.assessments.schemas import (
    AssessmentCreateSchema,
    AssessmentUpdateSchema,
    AssessmentResponseSchema,
    AssessmentQuerySchema,
    AssessmentPaginatedResponseSchema,
)
from app.assessments.service import (
    create_assessment,
    update_assessment,
    get_assessment_for_user,
    list_assessments_for_user,
    AssessmentNotFoundError,
    CourseNotFoundError,
    InvalidAssessmentError,
    DuplicateAssessmentError,
    AssessmentAccessDeniedError,
)


blp = Blueprint(
    "Assessments",
    __name__,
    url_prefix="/assessments",
    description="Assessment management.",
)


def get_current_user_role():
    """Get the authenticated user's current database role."""

    user = get_user_by_id(get_jwt_identity())

    if user is None or user.role is None:
        abort(401, message="Authenticated user or role was not found.")

    return user.role.role_name.strip().upper()


@blp.route("")
class AssessmentCollectionResource(MethodView):

    @blp.doc(
        summary="Create an assessment",
        description=(
            "ADMIN can create assessments for all courses. "
            "FACULTY can create assessments only for assigned courses."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssessmentCreateSchema)
    @blp.response(201, AssessmentResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, data):

        try:
            return create_assessment(
                data=data,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except CourseNotFoundError as exc:
            abort(404, message=str(exc))

        except DuplicateAssessmentError as exc:
            abort(409, message=str(exc))

        except InvalidAssessmentError as exc:
            abort(422, message=str(exc))

        except AssessmentAccessDeniedError as exc:
            abort(403, message=str(exc))


    @blp.doc(
        summary="List assessments",
        description=(
            "Returns paginated assessments. ADMIN can view all assessments. "
            "FACULTY can view assessments only for assigned courses. "
            "Supports filtering by course, assessment type, academic year "
            "and semester."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssessmentQuerySchema, location="query")
    @blp.response(200, AssessmentPaginatedResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, query_args):

        try:
            return list_assessments_for_user(
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
                page=query_args["page"],
                per_page=query_args["per_page"],
                course_id=query_args.get("course_id"),
                assessment_type=query_args.get("assessment_type"),
                academic_year=query_args.get("academic_year"),
                semester=query_args.get("semester"),
            )

        except AssessmentAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/<uuid:assessment_id>")
class AssessmentDetailResource(MethodView):

    @blp.doc(
        summary="Get assessment by UUID",
        description=(
            "ADMIN can view any assessment. FACULTY can view "
            "assessments belonging to assigned courses."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AssessmentResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, assessment_id):

        try:
            return get_assessment_for_user(
                assessment_id=assessment_id,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except AssessmentNotFoundError as exc:
            abort(404, message=str(exc))

        except AssessmentAccessDeniedError as exc:
            abort(403, message=str(exc))


    @blp.doc(
        summary="Update assessment",
        description=(
            "ADMIN can update any assessment. FACULTY can update "
            "assessments belonging to assigned courses."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssessmentUpdateSchema)
    @blp.response(200, AssessmentResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, assessment_id):

        try:
            return update_assessment(
                assessment_id=assessment_id,
                data=data,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except AssessmentNotFoundError as exc:
            abort(404, message=str(exc))

        except CourseNotFoundError as exc:
            abort(404, message=str(exc))

        except DuplicateAssessmentError as exc:
            abort(409, message=str(exc))

        except InvalidAssessmentError as exc:
            abort(422, message=str(exc))

        except AssessmentAccessDeniedError as exc:
            abort(403, message=str(exc))
