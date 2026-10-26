
from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        metadata={
            "description": "Registered user's email address.",
            "example": "admin@stubase.com",
        },
        error_messages={
            "required": "Email is required.",
            "invalid": "Enter a valid email address.",
        },
    )

    password = fields.String(
        required=True,
        load_only=True,
        metadata={
            "description": "The password associated with the account.",
            "example": "Admin@123",
        },
        validate=validate.Length(min=1, error="Password is required."),
        error_messages={"required": "Password is required."},
    )


class TokenResponseSchema(Schema):
    access_token = fields.String(
        required=True,
        metadata={
            "description": "Short-lived JWT used to access protected endpoints.",
            "example": "<access-token-returned-by-login>",
        },
    )
    refresh_token = fields.String(
        required=True,
        metadata={
            "description": "JWT used to obtain a new access token.",
            "example": "<refresh-token-returned-by-login>",
        },
    )
    token_type = fields.String(
        required=True,
        metadata={"description": "Authorization scheme.", "example": "Bearer"},
    )
    expires_in = fields.Integer(
        required=True,
        metadata={
            "description": "Access-token lifetime in seconds.",
            "example": 900,
        },
    )


class UserResponseSchema(Schema):
    id = fields.UUID(
        required=True,
        metadata={
            "description": "Unique user identifier (UUID).",
            "example": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )
    username = fields.String(
        required=True,
        metadata={"example": "admin"},
    )
    email = fields.Email(
        required=True,
        metadata={"example": "admin@stubase.com"},
    )
    role = fields.String(
        required=True,
        metadata={
            "description": "Role assigned to the account.",
            "example": "ADMIN",
        },
    )
    is_active = fields.Boolean(
        required=True,
        metadata={"example": True},
    )

    is_verified = fields.Boolean(
        required=True,
        metadata={"example": True},
    )


class LoginResponseSchema(Schema):
    message = fields.String(
        required=True,
        metadata={"example": "Login successful."},
    )

    user = fields.Nested(
        UserResponseSchema,
        required=True,
    )

    tokens = fields.Nested(
        TokenResponseSchema,
        required=True,
    )
    

class RefreshResponseSchema(Schema):
    access_token = fields.String(
        required=True,
        metadata={
            "description": "New access token. Use it as a Bearer token.",
            "example": "<new-access-token>",
        },
    )

    token_type = fields.String(
        required=True,
        metadata={"example": "Bearer"},
    )

    expires_in = fields.Integer(
        required=True,
        metadata={"example": 900},
    )


class ErrorResponseSchema(Schema):
    code = fields.Integer(
        metadata={"example": 401},
    )

    status = fields.String(
        metadata={"example": "Unauthorized"},
    )

    message = fields.String(
        metadata={"example": "Invalid email or password."},
    )

