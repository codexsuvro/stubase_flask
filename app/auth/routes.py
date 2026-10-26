
from flask_smorest import Blueprint, abort
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    create_access_token,
)
from flask import current_app
from app.auth.schemas import (
    LoginSchema,
    LoginResponseSchema,
    UserResponseSchema,
    RefreshResponseSchema,
    ErrorResponseSchema,
)
from app.auth.service import login_user, AuthenticationError
from app.auth.repository import get_user_by_id
from flask.views import MethodView


blp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
    description="Authentication, token management, and user identity endpoints",
)


@blp.route("/login")
class LoginResource(MethodView):
    @blp.doc(
        summary="Authenticate a user",
        description=(
            "Validates account credentials and returns an access token "
            "and a refresh token."
        ),
    )
    @blp.arguments(LoginSchema)
    @blp.response(200, LoginResponseSchema)
    @blp.alt_response(
        401,
        schema=ErrorResponseSchema,
        description="Credentials are invalid or the account cannot log in.",
    )
    def post(self, login_data):
        """Authenticate a user and return JWT tokens."""
        try:
            return login_user(
                email=login_data["email"],
                password=login_data["password"],
            )
        except AuthenticationError as exc:
            abort(401, message=str(exc))


@blp.route("/me")
class CurrentUserResource(MethodView):
    @jwt_required()
    @blp.doc(
        summary="Get current user",
        description="Returns the profile associated with the access token.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, UserResponseSchema)
    @blp.alt_response(
        401,
        schema=ErrorResponseSchema,
        description="Access token is missing, invalid, expired, or the user is unavailable.",
    )
    def get(self):
        """Return the currently authenticated user's profile."""
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)

        if user is None or not user.is_active or not user.is_verified:
            abort(401, message="User is unavailable or not authorized.")

        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.role_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }


@blp.route("/refresh")
class RefreshTokenResource(MethodView):
    @jwt_required(refresh=True)
    @blp.doc(
        summary="Refresh access token",
        description="Uses a valid refresh token to issue a new access token.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, RefreshResponseSchema)
    @blp.alt_response(
        401,
        schema=ErrorResponseSchema,
        description="Refresh token is missing, invalid, expired, or the user is unavailable.",
    )
    def post(self):
        """Generate a new access token using a refresh token."""
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)

        if user is None or not user.is_active or not user.is_verified:
            abort(401, message="User is unavailable or not authorized.")

        access_expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        expires_in = int(access_expires.total_seconds())

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role.role_name},
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
        }
