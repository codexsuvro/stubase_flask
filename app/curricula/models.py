from app.extensions import db
from app.models.base import BaseModel, UUIDMixin


class Curriculum(UUIDMixin, BaseModel):
    __tablename__ = "curriculums"

    __table_args__ = (
        db.UniqueConstraint(
            "department_id",
            "academic_year_id",
            "curriculum_code",
            "version",
            name="uq_curriculum_department_year_code_version",
        ),
        db.CheckConstraint(
            "version > 0",
            name="ck_curriculum_version",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')",
            name="ck_curriculum_status",
        ),
        db.CheckConstraint(
            "effective_until IS NULL OR effective_from < effective_until",
            name="ck_curriculum_effective_dates",
        ),
    )

    department_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )

    academic_year_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("academic_years.id"),
        nullable=False,
        index=True,
    )

    curriculum_code = db.Column(
        db.String(30),
        nullable=False,
    )

    curriculum_name = db.Column(
        db.String(150),
        nullable=False,
    )

    program_name = db.Column(
        db.String(100),
        nullable=False,
    )

    version = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    effective_from = db.Column(
        db.Date,
        nullable=False,
    )

    effective_until = db.Column(
        db.Date,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    department = db.relationship(
        "Department",
        back_populates="curriculums",
        lazy="selectin",
    )

    academic_year = db.relationship(
        "AcademicYear",
        back_populates="curriculums",
        lazy="selectin",
    )

    curriculum_courses = db.relationship(
        "CurriculumCourse",
        back_populates="curriculum",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CurriculumCourse(UUIDMixin, BaseModel):
    """Service validation must align year, department, and course/semester number."""

    __tablename__ = "curriculum_courses"

    __table_args__ = (
        db.UniqueConstraint(
            "curriculum_id",
            "course_id",
            name="uq_curriculum_course_course",
        ),
        db.UniqueConstraint(
            "curriculum_id",
            "semester_id",
            "sequence_order",
            name="uq_curriculum_course_semester_sequence",
        ),
        db.CheckConstraint(
            "sequence_order > 0",
            name="ck_curriculum_course_sequence_order",
        ),
        db.CheckConstraint(
            "credits_override IS NULL OR credits_override > 0",
            name="ck_curriculum_course_credits_override",
        ),
        db.CheckConstraint(
            "required_hours IS NULL OR required_hours >= 0",
            name="ck_curriculum_course_required_hours",
        ),
    )

    curriculum_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("curriculums.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )

    semester_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("semesters.id"),
        nullable=False,
        index=True,
    )

    sequence_order = db.Column(
        db.Integer,
        nullable=False,
    )

    credits_override = db.Column(
        db.Integer,
        nullable=True,
    )

    required_hours = db.Column(
        db.Numeric(6, 2),
        nullable=True,
    )

    curriculum = db.relationship(
        "Curriculum",
        back_populates="curriculum_courses",
        lazy="selectin",
    )

    course = db.relationship(
        "Course",
        back_populates="curriculum_courses",
        lazy="selectin",
    )

    semester = db.relationship(
        "Semester",
        back_populates="curriculum_courses",
        lazy="selectin",
    )

    syllabi = db.relationship(
        "Syllabus",
        back_populates="curriculum_course",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Syllabus(UUIDMixin, BaseModel):
    __tablename__ = "syllabi"

    __table_args__ = (
        db.UniqueConstraint(
            "curriculum_course_id",
            "version",
            name="uq_syllabus_curriculum_course_version",
        ),
        db.CheckConstraint(
            "version > 0",
            name="ck_syllabus_version",
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')",
            name="ck_syllabus_status",
        ),
    )

    curriculum_course_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("curriculum_courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(150),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    objectives = db.Column(
        db.Text,
        nullable=True,
    )

    version = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    curriculum_course = db.relationship(
        "CurriculumCourse",
        back_populates="syllabi",
        lazy="selectin",
    )

    units = db.relationship(
        "SyllabusUnit",
        back_populates="syllabus",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    learning_outcomes = db.relationship(
        "LearningOutcome",
        back_populates="syllabus",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SyllabusUnit(UUIDMixin, BaseModel):
    __tablename__ = "syllabus_units"

    __table_args__ = (
        db.UniqueConstraint(
            "syllabus_id",
            "unit_number",
            name="uq_syllabus_unit_number",
        ),
        db.UniqueConstraint(
            "syllabus_id",
            "sequence_order",
            name="uq_syllabus_unit_sequence",
        ),
        db.CheckConstraint(
            "unit_number > 0",
            name="ck_syllabus_unit_number",
        ),
        db.CheckConstraint(
            "sequence_order > 0",
            name="ck_syllabus_unit_sequence_order",
        ),
        db.CheckConstraint(
            "teaching_hours IS NULL OR teaching_hours >= 0",
            name="ck_syllabus_unit_teaching_hours",
        ),
    )

    syllabus_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("syllabi.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    unit_number = db.Column(
        db.Integer,
        nullable=False,
    )

    title = db.Column(
        db.String(150),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    sequence_order = db.Column(
        db.Integer,
        nullable=False,
    )

    teaching_hours = db.Column(
        db.Numeric(6, 2),
        nullable=True,
    )

    syllabus = db.relationship(
        "Syllabus",
        back_populates="units",
        lazy="selectin",
    )

    topics = db.relationship(
        "SyllabusTopic",
        back_populates="unit",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SyllabusTopic(UUIDMixin, BaseModel):
    __tablename__ = "syllabus_topics"

    __table_args__ = (
        db.UniqueConstraint(
            "unit_id",
            "sequence_order",
            name="uq_syllabus_topic_sequence",
        ),
        db.CheckConstraint(
            "sequence_order > 0",
            name="ck_syllabus_topic_sequence_order",
        ),
        db.CheckConstraint(
            "teaching_hours IS NULL OR teaching_hours >= 0",
            name="ck_syllabus_topic_teaching_hours",
        ),
    )

    unit_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("syllabus_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(200),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    sequence_order = db.Column(
        db.Integer,
        nullable=False,
    )

    teaching_hours = db.Column(
        db.Numeric(6, 2),
        nullable=True,
    )

    reference_url = db.Column(
        db.String(2048),
        nullable=True,
    )

    unit = db.relationship(
        "SyllabusUnit",
        back_populates="topics",
        lazy="selectin",
    )

    learning_outcome_mappings = db.relationship(
        "TopicLearningOutcome",
        back_populates="topic",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class LearningOutcome(UUIDMixin, BaseModel):
    __tablename__ = "learning_outcomes"

    __table_args__ = (
        db.UniqueConstraint(
            "syllabus_id",
            "outcome_code",
            name="uq_learning_outcome_syllabus_code",
        ),
    )

    syllabus_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("syllabi.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    outcome_code = db.Column(
        db.String(30),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    outcome_type = db.Column(
        db.String(50),
        nullable=True,
    )

    syllabus = db.relationship(
        "Syllabus",
        back_populates="learning_outcomes",
        lazy="selectin",
    )

    topic_mappings = db.relationship(
        "TopicLearningOutcome",
        back_populates="learning_outcome",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TopicLearningOutcome(UUIDMixin, BaseModel):
    """Topic/outcome mapping; the service layer must require a shared syllabus."""

    __tablename__ = "topic_learning_outcomes"

    __table_args__ = (
        db.UniqueConstraint(
            "topic_id",
            "learning_outcome_id",
            name="uq_topic_learning_outcome",
        ),
    )

    topic_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    learning_outcome_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("learning_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic = db.relationship(
        "SyllabusTopic",
        back_populates="learning_outcome_mappings",
        lazy="selectin",
    )

    learning_outcome = db.relationship(
        "LearningOutcome",
        back_populates="topic_mappings",
        lazy="selectin",
    )
