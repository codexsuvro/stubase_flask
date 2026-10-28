from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.users.schemas import UserResponseSchema, UserCreateSchema
from app.users.repository import list_users, get_user_by_uuid
from app.users.service import (
    create_user_account,
    UserAlreadyExistsError,
    InvalidRoleError,
    DepartmentNotFoundError,
)

blp = Blueprint(
    "Users",
    __name__,
    url_prefix="/users",
    description="User account and profile proviosioning.",
)

@blp.route("")
class UserCollectionResource(MethodView):
    @blp.doc(
        summary="Create a Faculty or Student account",
        description=(
            "ADMIN only. Creates the user account and its corresponding "
            "Faculty or Student profile in one transaction."
        ),
        security=[{"bearerAuth": []}],
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
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, UserResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        return list_users()
    
@blp.route("/<uuid:user_id>")
class UserDetailResource(MethodView):
    @blp.doc(
        summary="Get a user account by UUID",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, UserResponseSchema)
    @role_required("ADMIN")
    def get(self, user_id):
        user = get_user_by_uuid(user_id)
        if user is None:
            abort(404, message="User account not found")
        return user