from datetime import UTC, datetime

from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class TokenBlocklist(UUIDMixin, BaseModel):
    __tablename__ = "token_blocklist"

    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self):
        return f"<TokenBlocklist {self.jti} ({self.token_type})>"