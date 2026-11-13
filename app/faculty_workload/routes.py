from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity

from werkzeug.exceptions import (
    NotFound,
    Conflict,
    UnprocessableEntity,
)

from app.auth.permissions import role_required

from app.faculty_workload.schemas import (
    FacultyWorkloadQuerySchema,
    FacultyWorkloadPolicyFilterSchema,
    FacultyWorkloadPolicyCreateSchema,
    FacultyWorkloadPolicyUpdateSchema,
    FacultyWorkloadPolicyResponseSchema,
    FacultyWorkloadResponseSchema,
)

from app.faculty_workload.service import (
    calculate_faculty_workload,
    get_all_faculty_workloads,
    get_faculty_workload_for_user,
    create_workload_policy,
    update_workload_policy,
    get_all_workload_policies,
)


blp = Blueprint(
    "FacultyWorkload",
    __name__,
    url_prefix="/faculty-workload",
    description="Faculty teaching workload management.",
)


@blp.route("")
class FacultyWorkloadCollectionResource(MethodView):

    @blp.doc(
        summary="Get all faculty workloads",
        description=(
            "ADMIN only. Returns the weekly teaching workload "
            "of all faculty members for a semester."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        FacultyWorkloadQuerySchema,
        location="query",
    )
    @blp.response(
        200,
        FacultyWorkloadResponseSchema(many=True),
    )
    @role_required("ADMIN")
    def get(self, query_args):
        try:
            return get_all_faculty_workloads(
                query_args["semester_id"]
            )

        except NotFound as exc:
            abort(404, message=exc.description)


@blp.route("/me")
class MyFacultyWorkloadResource(MethodView):

    @blp.doc(
        summary="Get my teaching workload",
        description=(
            "FACULTY only. Returns the authenticated faculty "
            "member's own workload."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        FacultyWorkloadQuerySchema,
        location="query",
    )
    @blp.response(
        200,
        FacultyWorkloadResponseSchema,
    )
    @role_required("FACULTY")
    def get(self, query_args):
        try:
            return get_faculty_workload_for_user(
                get_jwt_identity(),
                query_args["semester_id"],
            )

        except NotFound as exc:
            abort(404, message=exc.description)


@blp.route("/<uuid:faculty_id>")
class FacultyWorkloadDetailResource(MethodView):

    @blp.doc(
        summary="Get workload of a faculty member",
        description="ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        FacultyWorkloadQuerySchema,
        location="query",
    )
    @blp.response(
        200,
        FacultyWorkloadResponseSchema,
    )
    @role_required("ADMIN")
    def get(self, query_args, faculty_id):
        try:
            return calculate_faculty_workload(
                faculty_id,
                query_args["semester_id"],
            )

        except NotFound as exc:
            abort(404, message=exc.description)


@blp.route("/policies")
class FacultyWorkloadPolicyCollectionResource(MethodView):

    @blp.doc(
        summary="List workload policies",
        description=(
            "ADMIN only. Supports faculty and semester filters."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        FacultyWorkloadPolicyFilterSchema,
        location="query",
    )
    @blp.response(
        200,
        FacultyWorkloadPolicyResponseSchema(many=True),
    )
    @role_required("ADMIN")
    def get(self, query_args):
        try:
            return get_all_workload_policies(
                faculty_id=query_args.get("faculty_id"),
                semester_id=query_args.get("semester_id"),
            )

        except NotFound as exc:
            abort(404, message=exc.description)

    @blp.doc(
        summary="Create a workload policy",
        description=(
            "ADMIN only. Creates minimum and maximum weekly "
            "teaching-hour limits for a faculty member."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FacultyWorkloadPolicyCreateSchema)
    @blp.response(
        201,
        FacultyWorkloadPolicyResponseSchema,
    )
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_workload_policy(data)

        except NotFound as exc:
            abort(404, message=exc.description)

        except Conflict as exc:
            abort(409, message=exc.description)

        except UnprocessableEntity as exc:
            abort(422, message=exc.description)


@blp.route("/policies/<uuid:policy_id>")
class FacultyWorkloadPolicyDetailResource(MethodView):

    @blp.doc(
        summary="Update a workload policy",
        description="ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FacultyWorkloadPolicyUpdateSchema)
    @blp.response(
        200,
        FacultyWorkloadPolicyResponseSchema,
    )
    @role_required("ADMIN")
    def patch(self, data, policy_id):
        try:
            return update_workload_policy(
                policy_id,
                data,
            )

        except NotFound as exc:
            abort(404, message=exc.description)

        except UnprocessableEntity as exc:
            abort(422, message=exc.description)