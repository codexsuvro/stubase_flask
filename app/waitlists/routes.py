from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity
from app.auth.permissions import role_required
from app.waitlists.schemas import (
    WaitlistJoinSchema,
    WaitlistResponseSchema,
    WaitlistPromotionResponseSchema,
)
from app.waitlists.service import (
    join_waitlist,
    get_my_waitlist,
    get_offering_waitlist,
    cancel_waitlist_entry,
    promote_next_student,
    WaitlistNotFoundError,
    WaitlistConflictError,
    InvalidWaitlistOperationError,
)


blp = Blueprint(
    "Waitlists",
    __name__,
    url_prefix="/waitlists",
    description="Course offering waitlist management.",
)


def handle_error(exc):

    if isinstance(exc, WaitlistNotFoundError):
        abort(404, message=str(exc))

    if isinstance(exc, WaitlistConflictError):
        abort(409, message=str(exc))

    if isinstance(exc, InvalidWaitlistOperationError):
        abort(422, message=str(exc))

    raise exc


@blp.route("")
class WaitlistCollectionResource(MethodView):

    @blp.doc(
        summary="Join a course offering waitlist",
        description=(
            "STUDENT only. The offering must be full and OPEN. "
            "Prerequisites are validated before joining."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(WaitlistJoinSchema)
    @blp.response(201, WaitlistResponseSchema)
    @role_required("STUDENT")
    def post(self, data):

        try:
            return join_waitlist(
                get_jwt_identity(),
                data["offering_id"],
            )

        except Exception as exc:
            handle_error(exc)

    @blp.doc(
        summary="List waitlist entries for an offering",
        description="ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(
        200,
        WaitlistResponseSchema(many=True),
    )
    @role_required("ADMIN")
    def get(self):

        from flask import request
        from uuid import UUID

        offering_id = request.args.get("offering_id")

        if not offering_id:
            abort(
                422,
                message="offering_id query parameter is required.",
            )

        try:
            offering_id = UUID(offering_id)

        except ValueError:
            abort(422, message="Invalid offering_id UUID.")

        try:
            return get_offering_waitlist(offering_id)

        except Exception as exc:
            handle_error(exc)


@blp.route("/my")
class MyWaitlistResource(MethodView):

    @blp.doc(
        summary="Get my waitlist entries",
        description="STUDENT only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(
        200,
        WaitlistResponseSchema(many=True),
    )
    @role_required("STUDENT")
    def get(self):

        try:
            return get_my_waitlist(
                get_jwt_identity()
            )

        except Exception as exc:
            handle_error(exc)


@blp.route("/<uuid:waitlist_id>")
class WaitlistDetailResource(MethodView):

    @blp.doc(
        summary="Cancel a waitlist entry",
        description=(
            "STUDENT can cancel their own WAITING entry. "
            "ADMIN can cancel any WAITING entry."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, WaitlistResponseSchema)
    @role_required("ADMIN", "STUDENT")
    def delete(self, waitlist_id):

        from app.auth.repository import get_user_by_id

        user = get_user_by_id(get_jwt_identity())

        role_name = user.role.role_name.upper()

        try:
            return cancel_waitlist_entry(
                waitlist_id,
                user_id=(
                    get_jwt_identity()
                    if role_name == "STUDENT"
                    else None
                ),
            )

        except Exception as exc:
            handle_error(exc)


@blp.route("/<uuid:offering_id>/promote")
class WaitlistPromotionResource(MethodView):

    @blp.doc(
        summary="Promote the next eligible student",
        description=(
            "ADMIN only. Promotes the earliest eligible WAITING student "
            "when the offering has an available seat."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(
        200,
        WaitlistPromotionResponseSchema,
    )
    @role_required("ADMIN")
    def post(self, offering_id):

        try:
            return promote_next_student(offering_id)

        except Exception as exc:
            handle_error(exc)