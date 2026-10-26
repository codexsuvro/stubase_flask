
from datetime import UTC, datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app.auth.repository import get_user_by_email
from app.extensions import db
from app.utils.security import check_password


class AuthenticationError(Exception):
    """Raised when authentication fails."""


def login_user(email: str, password: str) -> dict:
    """
    Authenticate a user and generate access and refresh tokens.
    """

    user = get_user_by_email(email.strip().lower())

    # Use the same message for unknown email and incorrect password.
    if user is None or not check_password(user.password_hash, password):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("Your account is inactive. Contact the administrator.")

    if not user.is_verified:
        raise AuthenticationError("Your account is not verified. Contact the administrator.")

    access_expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role.role_name,
        },
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
    )

    user.last_login = datetime.now(UTC)
    db.session.commit()

    expires_in = (
        int(access_expires.total_seconds())
        if isinstance(access_expires, timedelta)
        else int(access_expires)
    )

    return {
        "message": "Login successful.",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.role_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
        },
    }
