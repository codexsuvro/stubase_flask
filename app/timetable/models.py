
from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Classroom(UUIDMixin, BaseModel):

    __tablename__ = "classrooms"

    __table_args__ = (
        db.CheckConstraint(
            "capacity > 0",
            name="ck_classroom_capacity",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_classroom_status",
        ),
        db.UniqueConstraint(
            "building",
            "room_number",
            name="uq_classroom_building_room",
        ),
    )

    building = db.Column(
        db.String(100),
        nullable=False,
    )

    room_number = db.Column(
        db.String(30),
        nullable=False,
    )

    capacity = db.Column(
        db.Integer,
        nullable=False,
    )

    room_type = db.Column(
        db.String(30),
        nullable=False,
        default="CLASSROOM",
        server_default="CLASSROOM",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )

    timetable_slots = db.relationship(
        "TimetableSlot",
        back_populates="classroom",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<Classroom {self.building} "
            f"{self.room_number}>"
        )


class TimetableSlot(UUIDMixin, BaseModel):

    __tablename__ = "timetable_slots"

    __table_args__ = (
        db.CheckConstraint(
            "day_of_week BETWEEN 1 AND 7",
            name="ck_timetable_day_of_week",
        ),
        db.CheckConstraint(
            "start_time < end_time",
            name="ck_timetable_time_range",
        ),
        db.CheckConstraint(
            "status IN ('ACTIVE', 'CANCELLED')",
            name="ck_timetable_status",
        ),
        db.Index(
            "ix_timetable_faculty_day",
            "faculty_id",
            "day_of_week",
        ),
        db.Index(
            "ix_timetable_classroom_day",
            "classroom_id",
            "day_of_week",
        ),
        db.Index(
            "ix_timetable_offering_day",
            "offering_id",
            "day_of_week",
        ),
    )

    offering_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("course_offerings.id"),
        nullable=False,
        index=True,
    )

    faculty_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("faculties.id"),
        nullable=False,
        index=True,
    )

    classroom_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("classrooms.id"),
        nullable=False,
        index=True,
    )

    day_of_week = db.Column(
        db.Integer,
        nullable=False,
    )

    start_time = db.Column(
        db.Time,
        nullable=False,
    )

    end_time = db.Column(
        db.Time,
        nullable=False,
    )

    effective_from = db.Column(
        db.Date,
        nullable=False,
    )

    effective_until = db.Column(
        db.Date,
        nullable=False,
    )

    session_type = db.Column(
        db.String(30),
        nullable=False,
        default="LECTURE",
        server_default="LECTURE",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )

    remarks = db.Column(
        db.String(255),
        nullable=True,
    )

    offering = db.relationship(
        "CourseOffering",
        lazy="selectin",
    )

    faculty = db.relationship(
        "Faculty",
        lazy="selectin",
    )

    classroom = db.relationship(
        "Classroom",
        back_populates="timetable_slots",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<TimetableSlot {self.offering_id} "
            f"day={self.day_of_week}>"
        )
