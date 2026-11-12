from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class CoursePrerequisite(UUIDMixin, BaseModel):

    __tablename__ = "course_prerequisites"

    __table_args__ = (
        db.UniqueConstraint(
            "course_id",
            "prerequisite_course_id",
            name="uq_course_prerequisite",
        ),
        db.CheckConstraint(
            "course_id != prerequisite_course_id",
            name="ck_course_prerequisite_not_self",
        ),
    )

    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prerequisite_course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    course = db.relationship(
        "Course",
        foreign_keys=[course_id],
        lazy="selectin",
    )

    prerequisite_course = db.relationship(
        "Course",
        foreign_keys=[prerequisite_course_id],
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<CoursePrerequisite "
            f"{self.course_id} requires "
            f"{self.prerequisite_course_id}>"
        )