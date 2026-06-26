from app.extensions import db
from datetime import datetime, UTC
from uuid import uuid4

class BaseModel(db.Model):
    __abstract__ = True

    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(UTC), 
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

class UUIDMixin:
    __abstract__ = True

    id = db.Column(
        db.UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )