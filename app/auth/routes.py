
from flask_smorest import Blueprint, abort
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
    create_access_token,
    get_jwt,
    decode_token,
)
from flask_jwt_extended.exceptions import JWTExtendedException
from flask import current_app
from app.auth.schemas import (
    LoginSchema,
    LoginResponseSchema,
    AuthUserResponseSchema,
    RefreshResponseSchema,
    ErrorResponseSchema,
    LogoutSchema,
    LogoutResponseSchema,
    ChangePasswordSchema,
    ChangePasswordResponseSchema,
)
from app.auth.service import login_user, AuthenticationError
from app.auth.repository import get_user_by_id
from flask.views import MethodView
from datetime import UTC, datetime
from app.extensions import db
from app.models.token_blocklist import TokenBlocklist
from app.utils.security import hash_password, check_password
from sqlalchemy.exc import IntegrityError
from app.auth.permissions import role_required


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
    @blp.response(200, AuthUserResponseSchema)
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
            additional_claims={
                "role": user.role.role_name,
                "token_version": user.token_version,
            },
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
        }


@blp.route("/logout")
class LogoutResource(MethodView):
    @jwt_required()
    @blp.arguments(LogoutSchema)
    @blp.response(200, LogoutResponseSchema)
    @blp.alt_response(
        401,
        description="Access or refresh token is invalid, expired, revoked, or does not belong to the same user.",
    )
    @blp.doc(
        summary="Log out the current user",
        description=(
            "Revokes the current access token and the supplied refresh token. ",
            "The access token must be provided as a Bearer token."
        ),
        security=[{"bearerAuth": []}],
    )
    def post(self, logout_data):
        # The access token has already been validated by @jwt_required()
        access_claims = get_jwt()
        user_id = get_jwt_identity()
        refresh_token = logout_data["refresh_token"]
        
        # Decode and validate the refresh token's signature and expiry
        try:
            refresh_claims = decode_token(refresh_token)
        except JWTExtendedException:
            abort(401, message="Refresh token is invalid or expired.")
            
        # Make sure the supplied token is actually a refresh token
        if refresh_claims.get("type") != "refresh":
            abort(401, message="A valid refresh token is required.")
        
        # Both tokens must belong to the same user
        if refresh_claims.get("sub") != user_id:
            abort(401, message="Tokens do not belong to the same user.")
            
        access_jti = access_claims["jti"]
        refresh_jti = refresh_claims["jti"]
        
        # Reject a refresh token that has already been revoked.
        existing_refresh = db.session.scalar(
            db.select(TokenBlocklist.id).where(TokenBlocklist.jti == refresh_jti)
        )
        
        if existing_refresh is not None:
            abort(401, message="Refresh token has already been revoked.")
            
        # Store both tokens in the blocklist
        now = datetime.now(UTC)
        access_block = TokenBlocklist(
            jti=access_jti,
            token_type="access",
            user_id=user_id,
            expires_at=datetime.fromtimestamp(
                access_claims["exp"], tz=UTC
            ),
            revoked_at=now,
        )
        
        refresh_block = TokenBlocklist(
            jti=refresh_jti,
            token_type="refresh",
            user_id=user_id,
            expires_at=datetime.fromtimestamp(
                refresh_claims["exp"], tz=UTC
            ),
            revoked_at=now,
        )
        
        try:
            db.session.add_all([access_block, refresh_block])
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(401, message="One or both tokens have already been revoked.")
        except Exception:
            db.session.rollback()
            raise
        
        return {"message": "Logout successful."}
    
@blp.route("/change-password")
class ChangePasswordResource(MethodView):
    @jwt_required()
    @blp.arguments(ChangePasswordSchema)
    @blp.response(200, ChangePasswordResponseSchema)
    @blp.alt_response(
        400,
        description="The current password is incorrect or the new password is invalid.",
    )
    @blp.alt_response(
        401,
        description="The access token is missing, invalid, expired, or revoked."
    )
    @blp.doc(
        summary="Change the current user's password.",
        description=(
            "Requires a valid access token and the current password. "
            "Changing the password invalidates all previously issued tokens "
            "for this user. The user must log in again."
        ),
        security=[{"bearerAuth": []}],
    )
    def post(self, password_data):
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        
        if user is None or not user.is_active or not user.is_verified:
            abort(401, message="User is unavailable or not authorized.")
            
        if not check_password(user.password_hash, password_data["current_password"]):
            abort(400, message="Current password is incorrect.")
            
        new_password = password_data["new_password"]
        
        if check_password(user.password_hash, new_password):
            abort(400, message="New password must be different from the current password.")
            
        user.password_hash = hash_password(new_password)
        user.token_version += 1
        
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        
        return {
            "message": "Password changed successfully. Please login again."
        }

@blp.route("/admin-check")
class AdminCheckResource(MethodView):

    @jwt_required()
    @role_required("ADMIN")
    def get(self):
        return {
            "message": "Admin access granted."
        }, 200