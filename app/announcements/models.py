from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Announcement(UUIDMixin, BaseModel):
    __tablename__ = "announcements"

    __table_args__ = (
        db.CheckConstraint(
            "audience_type IN ('GLOBAL', 'COURSE')",
            name="ck_announcement_audience_type",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')",
            name="ck_announcement_status",
        ),
        db.CheckConstraint(
            "(audience_type = 'GLOBAL' AND offering_id IS NULL) OR "
            "(audience_type = 'COURSE' AND offering_id IS NOT NULL)",
            name="ck_announcement_audience_offering",
        ),
        db.CheckConstraint(
            "(status = 'PUBLISHED' AND published_at IS NOT NULL) OR "
            "(status != 'PUBLISHED')",
            name="ck_announcement_published_at",
        ),
        db.CheckConstraint(
            "(status = 'ARCHIVED' AND archived_at IS NOT NULL) OR "
            "(status != 'ARCHIVED' AND archived_at IS NULL)",
            name="ck_announcement_archived_at",
        ),
        db.CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_announcement_title_nonblank",
        ),
        db.CheckConstraint(
            "length(trim(body)) > 0",
            name="ck_announcement_body_nonblank",
        ),
        db.Index(
            "ix_announcement_status_created_at",
            "status",
            "created_at",
        ),
    )

    audience_type = db.Column(
        db.String(20),
        nullable=False,
    )

    offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    created_by = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(200),
        nullable=False,
    )

    body = db.Column(
        db.Text,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    published_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    archived_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        lazy="select",
    )

    offering = db.relationship(
        "CourseOffering",
        lazy="select",
    )

    notifications = db.relationship(
        "Notification",
        back_populates="announcement",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Announcement {self.title} "
            f"status={self.status}>"
        )
