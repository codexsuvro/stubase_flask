from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity
from app.auth.permissions import role_required
from app.auth.repository import get_user_by_id
from app.results.schemas import (
    AssessmentResultCreateSchema,
    AssessmentResultUpdateSchema,
    AssessmentResultQuerySchema,
    AssessmentResultResponseSchema,
    AssessmentResultPaginatedResponseSchema,
    AssessmentAnalyticsResponseSchema,
)
from app.results.service import (
    create_result,
    update_result,
    get_result_for_user,
    list_results_for_user,
    list_my_results,
    AssessmentNotFoundError,
    EnrollmentNotFoundError,
    AssessmentResultNotFoundError,
    InvalidAssessmentResultError,
    DuplicateAssessmentResultError,
    AssessmentResultAccessDeniedError,
    get_my_result_analytics,
    get_course_result_analytics,
    get_assessment_result_analytics,
)


blp = Blueprint(
    "Assessment Results",
    __name__,
    url_prefix="/results",
    description="Assessment results management.",
)


def get_current_user_role():

    user = get_user_by_id(get_jwt_identity())

    if user is None or user.role is None:

        abort(
            401,
            message="Authenticated user or role was not found.",
        )

    return user.role.role_name.strip().upper()


@blp.route("")
class AssessmentResultCollectionResource(MethodView):

    @blp.doc(
        summary="Create an assessment result",
        description=(
            "ADMIN can create results for all offerings. "
            "FACULTY can create results only for their assigned offerings."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssessmentResultCreateSchema)
    @blp.response(201, AssessmentResultResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, data):

        try:
            return create_result(
                data=data,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except AssessmentNotFoundError as exc:
            abort(404, message=str(exc))

        except EnrollmentNotFoundError as exc:
            abort(404, message=str(exc))

        except DuplicateAssessmentResultError as exc:
            abort(409, message=str(exc))

        except InvalidAssessmentResultError as exc:
            abort(422, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


    @blp.doc(
        summary="List assessment results",
        description=(
            "ADMIN can view all results. FACULTY can view results "
            "belonging to their assigned course offerings."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        AssessmentResultQuerySchema,
        location="query",
    )
    @blp.response(
        200,
        AssessmentResultPaginatedResponseSchema,
    )
    @role_required("ADMIN", "FACULTY")
    def get(self, args):

        try:

            return list_results_for_user(
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
                **args,
            )

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/my")
class MyAssessmentResultsResource(MethodView):

    @blp.doc(
        summary="Get my assessment results",
        description=(
            "Students can view only their own assessment results. "
            "The student profile is resolved from the authenticated user."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        AssessmentResultQuerySchema,
        location="query",
    )
    @blp.response(
        200,
        AssessmentResultPaginatedResponseSchema,
    )
    @role_required("STUDENT")
    def get(self, args):

        try:

            return list_my_results(
                actor_user_id=get_jwt_identity(),
                page=args["page"],
                per_page=args["per_page"],
                assessment_id=args.get("assessment_id"),
            )

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/<uuid:result_id>")
class AssessmentResultDetailResource(MethodView):

    @blp.doc(
        summary="Get assessment result by UUID",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AssessmentResultResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, result_id):

        try:
            return get_result_for_user(
                result_id=result_id,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except AssessmentResultNotFoundError as exc:
            abort(404, message=str(exc))

        except InvalidAssessmentResultError as exc:
            abort(422, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


    @blp.doc(
        summary="Update assessment result",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssessmentResultUpdateSchema)
    @blp.response(200, AssessmentResultResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, result_id):

        try:
            return update_result(
                result_id=result_id,
                data=data,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except AssessmentResultNotFoundError as exc:
            abort(404, message=str(exc))

        except InvalidAssessmentResultError as exc:
            abort(422, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/assessment/<uuid:assessment_id>")
class AssessmentResultByAssessmentResource(MethodView):

    @blp.doc(
        summary="List results by assessment",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        AssessmentResultQuerySchema,
        location="query",
    )
    @blp.response(
        200,
        AssessmentResultPaginatedResponseSchema,
    )
    @role_required("ADMIN", "FACULTY")
    def get(self, args, assessment_id):

        try:

            return list_results_for_user(
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
                page=args["page"],
                per_page=args["per_page"],
                assessment_id=assessment_id,
                course_id=args.get("course_id"),
            )

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/enrollment/<uuid:enrollment_id>")
class AssessmentResultByEnrollmentResource(MethodView):

    @blp.doc(
        summary="List results by enrollment",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        AssessmentResultQuerySchema,
        location="query",
    )
    @blp.response(
        200,
        AssessmentResultPaginatedResponseSchema,
    )
    @role_required("ADMIN", "FACULTY")
    def get(self, args, enrollment_id):

        try:

            return list_results_for_user(
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
                page=args["page"],
                per_page=args["per_page"],
                enrollment_id=enrollment_id,
                course_id=args.get("course_id"),
            )

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))
            
            
@blp.route("/analytics/my")
class MyResultAnalyticsResource(MethodView):

    @blp.doc(
        summary="Get my academic performance analytics",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AssessmentAnalyticsResponseSchema)
    @role_required("STUDENT")
    def get(self):

        try:
            return get_my_result_analytics(
                actor_user_id=get_jwt_identity(),
            )

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/analytics/course/<uuid:course_id>")
class CourseResultAnalyticsResource(MethodView):

    @blp.doc(
        summary="Get course result analytics",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AssessmentAnalyticsResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, course_id):

        try:
            return get_course_result_analytics(
                course_id=course_id,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except AssessmentNotFoundError as exc:
            abort(404, message=str(exc))

        except InvalidAssessmentResultError as exc:
            abort(422, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))


@blp.route("/analytics/assessment/<uuid:assessment_id>")
class AssessmentResultAnalyticsResource(MethodView):

    @blp.doc(
        summary="Get assessment result analytics",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AssessmentAnalyticsResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, assessment_id):

        try:
            return get_assessment_result_analytics(
                assessment_id=assessment_id,
                actor_user_id=get_jwt_identity(),
                actor_role=get_current_user_role(),
            )

        except AssessmentNotFoundError as exc:
            abort(404, message=str(exc))

        except InvalidAssessmentResultError as exc:
            abort(422, message=str(exc))

        except AssessmentResultAccessDeniedError as exc:
            abort(403, message=str(exc))

