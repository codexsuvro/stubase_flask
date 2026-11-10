from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.users.schemas import (
    UserResponseSchema,
    UserCreateSchema,
    UserStatusUpdateSchema,
    UserVerificationUpdateSchema,
)
from app.users.repository import (
    list_users,
    get_user_by_uuid,
)
from app.users.service import (
    create_user_account,
    update_user_status,
    update_user_verification,
    UserAlreadyExistsError,
    InvalidRoleError,
    DepartmentNotFoundError,
    UserNotFoundError,
    LastActiveAdminError,
)

blp = Blueprint(
    "Users",
    __name__,
    url_prefix="/users",
    description="User account and profile provisioning.",
)

@blp.route("")
class UserCollectionResource(MethodView):
    @blp.doc(
        summary="Create a Faculty or Student account",
        description="Creates a user account with its corresponding profile. ADMIN only.",
    )
    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_user_account(data)
        except UserAlreadyExistsError as exc:
            abort(409, message=str(exc))
        except InvalidRoleError as exc:
            abort(400, message=str(exc))
        except DepartmentNotFoundError as exc:
            abort(404, message=str(exc))
        except ValueError as exc:
            abort(400, message=str(exc))

    @blp.doc(
        summary="List all user accounts",
        description="Returns all user accounts. ADMIN only.",
    )
    @blp.response(200, UserResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        return list_users()


@blp.route("/<uuid:user_id>")
class UserDetailResource(MethodView):
    @blp.doc(
        summary="Get a user account by UUID",
        description="Returns a user account using its UUID. ADMIN only.",
    )
    @blp.response(200, UserResponseSchema)
    @role_required("ADMIN")
    def get(self, user_id):
        user = get_user_by_uuid(user_id)
        if user is None:
            abort(404, message="User account not found.")

        return user


@blp.route("/<uuid:user_id>/status")
class UserStatusResource(MethodView):
    @blp.doc(
        summary="Activate or deactivate a user account",
        description=(
            "Updates the active status of a user account. "
            "Changing the status invalidates all previously issued JWTs. "
            "ADMIN only."
        ),
    )
    @blp.arguments(UserStatusUpdateSchema)
    @blp.response(200, UserResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, user_id):
        try:
            return update_user_status(
                user_id=user_id,
                is_active=data["is_active"],
            )
        except UserNotFoundError as exc:
            abort(404, message=str(exc))
        except LastActiveAdminError as exc:
            abort(409, message=str(exc))


@blp.route("/<uuid:user_id>/verification")
class UserVerificationResource(MethodView):
    @blp.doc(
        summary="Verify or unverify a user account",
        description=(
            "Updates the verification status of a user account. "
            "Changing the status invalidates all previously issued JWTs. "
            "ADMIN only."
        ),
    )
    @blp.arguments(UserVerificationUpdateSchema)
    @blp.response(200, UserResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, user_id):
        try:
            return update_user_verification(
                user_id=user_id,
                is_verified=data["is_verified"],
            )

        except UserNotFoundError as exc:
            abort(404, message=str(exc))

        except LastActiveAdminError as exc:
            abort(409, message=str(exc))