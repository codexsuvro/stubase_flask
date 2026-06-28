from app.extensions import db
from app.models.base import BaseModel, UUIDMixin

class User(UUIDMixin, BaseModel):
    
    __tablename__ = "users"

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )
    
    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )
    
    last_login = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    role_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("roles.id"),
        nullable=False,
    )

    role = db.relationship(
        'Role', 
        back_populates='users', 
        lazy='selectin',
    )
    
    student = db.relationship(
        "Student",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )

    faculty = db.relationship(
        "Faculty",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    
    def __repr__(self):
        return (
            f"<User {self.username} "
            f"{self.email}>"
        )