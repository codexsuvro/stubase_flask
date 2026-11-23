from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Notification(UUIDMixin, BaseModel):
    __tablename__ = "notifications"

    __table_args__ = (
        db.UniqueConstraint(
            "recipient_id",
            "announcement_id",
            name="uq_notification_recipient_announcement",
        ),
        db.CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_notification_title_nonblank",
        ),
        db.CheckConstraint(
            "length(trim(message)) > 0",
            name="ck_notification_message_nonblank",
        ),
        db.Index(
            "ix_notification_recipient_created_at",
            "recipient_id",
            "created_at",
        ),
        db.Index(
            "ix_notification_recipient_read_at",
            "recipient_id",
            "read_at",
        ),
    )

    recipient_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    announcement_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        default="ANNOUNCEMENT",
        server_default="ANNOUNCEMENT",
    )

    title = db.Column(
        db.String(200),
        nullable=False,
    )

    message = db.Column(
        db.Text,
        nullable=False,
    )

    read_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    recipient = db.relationship(
        "User",
        back_populates="notifications",
        lazy="select",
    )

    announcement = db.relationship(
        "Announcement",
        back_populates="notifications",
        lazy="select",
    )

    deliveries = db.relationship(
        "NotificationDelivery",
        back_populates="notification",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Notification {self.notification_type} "
            f"recipient={self.recipient_id}>"
        )


class NotificationDelivery(UUIDMixin, BaseModel):
    __tablename__ = "notification_deliveries"

    __table_args__ = (
        db.UniqueConstraint(
            "notification_id",
            "channel",
            name="uq_notification_delivery_channel",
        ),
        db.CheckConstraint(
            "channel IN ('EMAIL')",
            name="ck_notification_delivery_channel",
        ),
        db.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'SENT', 'FAILED')",
            name="ck_notification_delivery_status",
        ),
        db.CheckConstraint(
            "attempt_count >= 0",
            name="ck_notification_delivery_attempt_count",
        ),
        db.CheckConstraint(
            "(status = 'PROCESSING' AND locked_until IS NOT NULL) OR "
            "(status != 'PROCESSING' AND locked_until IS NULL)",
            name="ck_notification_delivery_lock_state",
        ),
        db.Index(
            "ix_notification_delivery_queue",
            "status",
            "next_attempt_at",
        ),
    )

    notification_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
    )

    channel = db.Column(
        db.String(20),
        nullable=False,
        default="EMAIL",
        server_default="EMAIL",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )

    attempt_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    next_attempt_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    locked_until = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    sent_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    last_error = db.Column(
        db.String(500),
        nullable=True,
    )

    notification = db.relationship(
        "Notification",
        back_populates="deliveries",
        lazy="select",
    )

    def __repr__(self):
        return (
            f"<NotificationDelivery {self.channel} "
            f"status={self.status}>"
        )
