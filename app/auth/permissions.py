from functools import wraps
from flask_jwt_extended import (
    get_jwt_identity,
    verify_jwt_in_request,
)
from flask_smorest import abort
from app.auth.repository import get_user_by_id


ALLOWED_ROLES = {"ADMIN", "FACULTY", "STUDENT"}


def role_required(*allowed_roles: str):
    """
    Restrict an endpoint using the user's current database role.

    Example:
        @role_required("ADMIN")
        @role_required("ADMIN", "FACULTY")
    """

    normalized_roles = {
        role.strip().upper()
        for role in allowed_roles
        if role and role.strip()
    }

    if not normalized_roles:
        raise ValueError("At least one allowed role must be provided.")

    invalid_roles = normalized_roles - ALLOWED_ROLES

    if invalid_roles:
        raise ValueError(
            f"Unsupported role(s): {', '.join(sorted(invalid_roles))}"
        )

    def decorator(view_function):
        @wraps(view_function)
        def wrapped(*args, **kwargs):
            # Validate JWT signature, expiry, token type and blocklist.
            verify_jwt_in_request()

            user_id = get_jwt_identity()
            user = get_user_by_id(user_id)

            if user is None:
                abort(401, message="Authenticated user was not found.")

            if not user.is_active:
                abort(401, message="Your account is inactive.")

            if not user.is_verified:
                abort(401, message="Your account is not verified.")

            # Always use the current database role, not the JWT role claim.
            current_role = (
                user.role.role_name.strip().upper()
                if user.role and user.role.role_name
                else None
            )

            if current_role not in normalized_roles:
                abort(
                    403,
                    message="You do not have permission to access this resource.",
                )

            return view_function(*args, **kwargs)

        return wrapped

    return decorator
