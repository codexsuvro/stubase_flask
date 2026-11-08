from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity
from app.auth.permissions import role_required
from app.results.schemas import (
    AssessmentResultCreateSchema,
    AssessmentResultUpdateSchema,
    AssessmentResultResponseSchema,
)
from app.results.service import (
    create_result,
    update_result,
    get_result_for_user,
    list_results_for_user,
    AssessmentNotFoundError,
    EnrollmentNotFoundError,
    AssessmentResultNotFoundError,
    InvalidAssessmentResultError,
    DuplicateAssessmentResultError,
    AssessmentResultAccessDeniedError,
)


blp = Blueprint(
    "Assessment Results",
    "results",
    url_prefix="/results",
    description="Assessment results management operations.",
)


@blp.route("/")
class AssessmentResultListResource(MethodView):

    @blp.arguments(AssessmentResultCreateSchema)
    @blp.response(201, AssessmentResultResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, data):
        """Create an assessment result."""

        actor_user_id = get_jwt_identity()
        actor_role = self.current_user.role.role_name

        try:
            return create_result(
                data,
                actor_user_id,
                actor_role,
            )

        except AssessmentNotFoundError as exc:
            abort(404, message=str(exc))

        except EnrollmentNotFoundError as exc:
            abort(404, message=str(exc))

        except InvalidAssessmentResultError as exc:
            abort(422, message=str(exc))

        except DuplicateAssessmentResultError as exc:
            abort(409, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))

    @blp.response(200, AssessmentResultResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        """List assessment results (ADMIN only)."""

        actor_user_id = get_jwt_identity()
        actor_role = self.current_user.role.role_name

        try:
            result = list_results_for_user(
                actor_user_id=actor_user_id,
                actor_role=actor_role,
            )

            return result["items"]

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/<uuid:result_id>")
class AssessmentResultResource(MethodView):

    @blp.response(200, AssessmentResultResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, result_id):
        """Get an assessment result."""

        actor_user_id = get_jwt_identity()
        actor_role = self.current_user.role.role_name

        try:
            return get_result_for_user(
                result_id,
                actor_user_id,
                actor_role,
            )

        except AssessmentResultNotFoundError as exc:
            abort(404, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))

    @blp.arguments(AssessmentResultUpdateSchema)
    @blp.response(200, AssessmentResultResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, result_id):
        """Update an assessment result."""

        actor_user_id = get_jwt_identity()
        actor_role = self.current_user.role.role_name

        try:
            return update_result(
                result_id,
                data,
                actor_user_id,
                actor_role,
            )

        except AssessmentResultNotFoundError as exc:
            abort(404, message=str(exc))

        except InvalidAssessmentResultError as exc:
            abort(422, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/assessment/<uuid:assessment_id>")
class AssessmentResultByAssessmentResource(MethodView):

    @blp.response(200, AssessmentResultResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY")
    def get(self, assessment_id):
        """Get results for an assessment."""

        actor_user_id = get_jwt_identity()
        actor_role = self.current_user.role.role_name

        try:
            assessment_results = list_results_for_user(
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                assessment_id=assessment_id,
            )

            return assessment_results["items"]

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/enrollment/<uuid:enrollment_id>")
class AssessmentResultByEnrollmentResource(MethodView):

    @blp.response(200, AssessmentResultResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY")
    def get(self, enrollment_id):
        """Get results for an enrollment."""

        actor_user_id = get_jwt_identity()
        actor_role = self.current_user.role.role_name

        try:
            assessment_results = list_results_for_user(
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                enrollment_id=enrollment_id,
            )

            return assessment_results["items"]

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


