from app.extensions import db
from app.models.base import BaseModel, UUIDMixin

class User(UUIDMixin, BaseModel):
    
    __tablename__ = "users"

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    role_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("roles.id"),
        nullable=False
    )

    role = db.relationship(
        'Role', 
        back_populates='users', 
        lazy='selectin'
    )