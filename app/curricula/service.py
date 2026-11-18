from sqlalchemy.exc import IntegrityError

from app.curricula.models import (
    Curriculum,
    CurriculumCourse,
    LearningOutcome,
    Syllabus,
    SyllabusTopic,
    SyllabusUnit,
    TopicLearningOutcome,
)
from app.curricula.repository import (
    CurriculumCourseRepository,
    CurriculumRepository,
    LearningOutcomeRepository,
    SyllabusRepository,
    SyllabusTopicRepository,
    SyllabusUnitRepository,
    TopicLearningOutcomeRepository,
)
from app.extensions import db
from app.models.academic_year import AcademicYear
from app.models.course import Course
from app.models.department import Department
from app.models.semester import Semester


class CurriculumModuleError(Exception):
    status_code = 422


class ResourceNotFoundError(CurriculumModuleError):
    status_code = 404


class ResourceConflictError(CurriculumModuleError):
    status_code = 409


class InvalidResourceStateError(CurriculumModuleError):
    status_code = 409


class ResourceAccessDeniedError(CurriculumModuleError):
    status_code = 403


def _require_department(department_id):
    department = db.session.get(Department, department_id)
    if department is None:
        raise ResourceNotFoundError("Department not found.")
    return department


def _require_academic_year(academic_year_id):
    academic_year = db.session.get(AcademicYear, academic_year_id)
    if academic_year is None:
        raise ResourceNotFoundError("Academic year not found.")
    return academic_year


def _validate_effective_dates(academic_year, start, end):
    if end is not None and start >= end:
        raise ValueError("effective_until must be later than effective_from.")
    if start < academic_year.start_date or start >= academic_year.end_date:
        raise ValueError(
            "effective_from must fall within the academic year."
        )
    if end is not None and end > academic_year.end_date:
        raise ValueError(
            "effective_until cannot extend beyond the academic year."
        )


def _check_curriculum_unique(
    department_id,
    academic_year_id,
    code,
    version,
    exclude_id=None,
):
    existing = CurriculumRepository.get_by_unique_key(
        department_id,
        academic_year_id,
        code,
        version,
    )
    if existing is not None and existing.id != exclude_id:
        raise ResourceConflictError(
            "A curriculum with this department, academic year, code, "
            "and version already exists."
        )


def _persist(repository_method, instance, conflict_message):
    try:
        return repository_method(instance)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(conflict_message) from exc


def create_curriculum(data):
    department = _require_department(data["department_id"])
    academic_year = _require_academic_year(data["academic_year_id"])
    code = data["curriculum_code"].strip().upper()
    version = data.get("version", 1)
    _validate_effective_dates(
        academic_year,
        data["effective_from"],
        data.get("effective_until"),
    )
    _check_curriculum_unique(
        department.id,
        academic_year.id,
        code,
        version,
    )
    curriculum = Curriculum(
        department_id=department.id,
        academic_year_id=academic_year.id,
        curriculum_code=code,
        curriculum_name=data["curriculum_name"].strip(),
        program_name=data["program_name"].strip(),
        version=version,
        description=data.get("description"),
        effective_from=data["effective_from"],
        effective_until=data.get("effective_until"),
        status="DRAFT",
    )
    return _persist(
        CurriculumRepository.create,
        curriculum,
        "Curriculum code and version already exist for this department and academic year.",
    )


def get_curriculum(curriculum_id, actor_role="ADMIN"):
    curriculum = CurriculumRepository.get_by_id(curriculum_id)
    if curriculum is None:
        raise ResourceNotFoundError("Curriculum not found.")
    if actor_role != "ADMIN" and curriculum.status != "PUBLISHED":
        raise ResourceNotFoundError("Curriculum not found.")
    return curriculum


def _require_curriculum_course(curriculum_course_id):
    curriculum_course = CurriculumCourseRepository.get_by_id(
        curriculum_course_id
    )
    if curriculum_course is None:
        raise ResourceNotFoundError("Curriculum course not found.")
    return curriculum_course


def _curriculum_for_course(entry):
    return get_curriculum(entry.curriculum_id)


def list_curriculums(
    actor_role,
    page=1,
    per_page=10,
    department_id=None,
    academic_year_id=None,
    status=None,
    curriculum_code=None,
):
    return CurriculumRepository.list_paginated(
        page=page,
        per_page=per_page,
        department_id=department_id,
        academic_year_id=academic_year_id,
        status=status,
        curriculum_code=curriculum_code,
        published_only=actor_role != "ADMIN",
    )


def update_curriculum(curriculum_id, data):
    curriculum = get_curriculum(curriculum_id)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "Only DRAFT curriculums can be updated."
        )

    department_id = data.get("department_id", curriculum.department_id)
    academic_year_id = data.get(
        "academic_year_id",
        curriculum.academic_year_id,
    )
    department = _require_department(department_id)
    academic_year = _require_academic_year(academic_year_id)
    if (
        department.id != curriculum.department_id
        or academic_year.id != curriculum.academic_year_id
    ) and CurriculumCourseRepository.list_by_curriculum(curriculum.id):
        raise InvalidResourceStateError(
            "Department and academic year cannot change after courses "
            "have been assigned."
        )

    start = data.get("effective_from", curriculum.effective_from)
    end = data.get("effective_until", curriculum.effective_until)
    _validate_effective_dates(academic_year, start, end)

    code = data.get("curriculum_code", curriculum.curriculum_code).strip().upper()
    version = data.get("version", curriculum.version)
    _check_curriculum_unique(
        department.id,
        academic_year.id,
        code,
        version,
        exclude_id=curriculum.id,
    )

    curriculum.department_id = department.id
    curriculum.academic_year_id = academic_year.id
    curriculum.curriculum_code = code
    curriculum.version = version
    curriculum.curriculum_name = data.get(
        "curriculum_name",
        curriculum.curriculum_name,
    ).strip()
    curriculum.program_name = data.get(
        "program_name",
        curriculum.program_name,
    ).strip()
    curriculum.description = data.get(
        "description",
        curriculum.description,
    )
    curriculum.effective_from = start
    curriculum.effective_until = end
    return _persist(
        CurriculumRepository.save,
        curriculum,
        "Curriculum code and version already exist for this department and academic year.",
    )


def delete_curriculum(curriculum_id):
    curriculum = get_curriculum(curriculum_id)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "Only DRAFT curriculums can be deleted."
        )
    entries = CurriculumCourseRepository.list_by_curriculum(curriculum.id)
    for entry in entries:
        if any(syllabus.status != "DRAFT" for syllabus in entry.syllabi):
            raise InvalidResourceStateError(
                "A curriculum containing a published or archived syllabus "
                "cannot be deleted."
            )
    try:
        CurriculumRepository.delete(curriculum)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(
            "Curriculum could not be deleted while it is referenced."
        ) from exc


def _syllabus_is_complete(syllabus):
    units = SyllabusUnitRepository.list_by_syllabus(syllabus.id)
    if not units:
        return False

    outcomes = LearningOutcomeRepository.list_by_syllabus(syllabus.id)
    if not outcomes:
        return False

    topics = [
        topic
        for unit in units
        for topic in SyllabusTopicRepository.list_by_unit(unit.id)
    ]
    if not topics:
        return False

    topic_mappings = {
        topic.id: TopicLearningOutcomeRepository.list_by_topic(topic.id)
        for topic in topics
    }
    if any(not mappings for mappings in topic_mappings.values()):
        return False

    mapped_outcome_ids = {
        mapping.learning_outcome_id
        for mappings in topic_mappings.values()
        for mapping in mappings
    }
    return all(outcome.id in mapped_outcome_ids for outcome in outcomes)


def publish_curriculum(curriculum_id):
    curriculum = get_curriculum(curriculum_id)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "Only DRAFT curriculums can be published."
        )
    entries = CurriculumCourseRepository.list_by_curriculum(curriculum.id)
    if not entries:
        raise InvalidResourceStateError(
            "A curriculum must contain at least one course before publishing."
        )
    for entry in entries:
        published_syllabi = [
            syllabus
            for syllabus in SyllabusRepository.list_by_curriculum_course(
                entry.id
            )
            if syllabus.status == "PUBLISHED"
        ]
        if not any(_syllabus_is_complete(item) for item in published_syllabi):
            raise InvalidResourceStateError(
                "Every curriculum course must have a complete PUBLISHED "
                "syllabus before the curriculum can be published."
            )
    curriculum.status = "PUBLISHED"
    return _persist(
        CurriculumRepository.save,
        curriculum,
        "Curriculum could not be published.",
    )


def archive_curriculum(curriculum_id):
    curriculum = get_curriculum(curriculum_id)
    if curriculum.status != "PUBLISHED":
        raise InvalidResourceStateError(
            "Only PUBLISHED curriculums can be archived."
        )
    curriculum.status = "ARCHIVED"
    return _persist(
        CurriculumRepository.save,
        curriculum,
        "Curriculum could not be archived.",
    )


def _require_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        raise ResourceNotFoundError("Course not found.")
    return course


def _require_semester(semester_id):
    semester = db.session.get(Semester, semester_id)
    if semester is None:
        raise ResourceNotFoundError("Semester not found.")
    return semester


def _validate_course_assignment(curriculum, course, semester):
    if course.department_id != curriculum.department_id:
        raise ValueError(
            "Course and curriculum must belong to the same department."
        )
    if semester.academic_year_id != curriculum.academic_year_id:
        raise ValueError(
            "Semester and curriculum must belong to the same academic year."
        )
    if course.semester != semester.semester_number:
        raise ValueError(
            "Course semester number must match the selected semester."
        )


def create_curriculum_course(curriculum_id, data):
    curriculum = get_curriculum(curriculum_id)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "Courses can be added only to a DRAFT curriculum."
        )
    course = _require_course(data["course_id"])
    semester = _require_semester(data["semester_id"])
    _validate_course_assignment(curriculum, course, semester)
    existing = CurriculumCourseRepository.get_by_course(
        curriculum.id,
        course.id,
    )
    if existing is not None:
        raise ResourceConflictError(
            "Course is already assigned to this curriculum."
        )
    sequence = data["sequence_order"]
    if sequence < 1:
        raise ValueError("sequence_order must be positive.")
    if CurriculumCourseRepository.get_by_sequence(
        curriculum.id,
        semester.id,
        sequence,
    ) is not None:
        raise ResourceConflictError(
            "This sequence position is already used in the semester."
        )
    credits = data.get("credits_override")
    if credits is not None and credits <= 0:
        raise ValueError("credits_override must be a positive integer.")
    hours = data.get("required_hours")
    if hours is not None and hours < 0:
        raise ValueError("required_hours cannot be negative.")
    entry = CurriculumCourse(
        curriculum_id=curriculum.id,
        course_id=course.id,
        semester_id=semester.id,
        sequence_order=sequence,
        credits_override=credits,
        required_hours=hours,
    )
    return _persist(
        CurriculumCourseRepository.create,
        entry,
        "Course assignment conflicts with an existing curriculum course or sequence.",
    )


def get_curriculum_course(curriculum_course_id, actor_role="ADMIN"):
    entry = CurriculumCourseRepository.get_by_id(curriculum_course_id)
    if entry is None:
        raise ResourceNotFoundError("Curriculum course not found.")
    get_curriculum(entry.curriculum_id, actor_role)
    return entry


def list_curriculum_courses(curriculum_id, actor_role="ADMIN"):
    get_curriculum(curriculum_id, actor_role)
    return CurriculumCourseRepository.list_by_curriculum(curriculum_id)


def remove_curriculum_course(curriculum_id, curriculum_course_id):
    curriculum = get_curriculum(curriculum_id)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "Courses can be removed only from a DRAFT curriculum."
        )
    entry = CurriculumCourseRepository.get_by_id(curriculum_course_id)
    if entry is None or entry.curriculum_id != curriculum.id:
        raise ResourceNotFoundError("Curriculum course not found.")
    if any(syllabus.status != "DRAFT" for syllabus in entry.syllabi):
        raise InvalidResourceStateError(
            "A course with a published or archived syllabus cannot be removed."
        )
    try:
        CurriculumCourseRepository.delete(entry)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(
            "Curriculum course could not be removed while it is referenced."
        ) from exc


def _require_syllabus(syllabus_id):
    syllabus = SyllabusRepository.get_by_id(syllabus_id)
    if syllabus is None:
        raise ResourceNotFoundError("Syllabus not found.")
    return syllabus


def _curriculum_for_syllabus(syllabus):
    entry = _require_curriculum_course(syllabus.curriculum_course_id)
    return get_curriculum(entry.curriculum_id), entry


def _require_visible_syllabus(syllabus_id, actor_role):
    syllabus = _require_syllabus(syllabus_id)
    curriculum, _ = _curriculum_for_syllabus(syllabus)
    if actor_role != "ADMIN" and (
        curriculum.status != "PUBLISHED"
        or syllabus.status != "PUBLISHED"
    ):
        raise ResourceNotFoundError("Syllabus not found.")
    return syllabus


def _require_draft_syllabus(syllabus):
    curriculum, _ = _curriculum_for_syllabus(syllabus)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "Syllabus content can be changed only while its curriculum is DRAFT."
        )
    if syllabus.status != "DRAFT":
        raise InvalidResourceStateError(
            "Only DRAFT syllabi can be modified."
        )
    return curriculum


def _require_visible_unit(unit_id, actor_role):
    unit = SyllabusUnitRepository.get_by_id(unit_id)
    if unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    syllabus = _require_visible_syllabus(unit.syllabus_id, actor_role)
    return unit, syllabus


def _require_draft_unit(unit):
    syllabus = _require_syllabus(unit.syllabus_id)
    _require_draft_syllabus(syllabus)
    return syllabus


def _require_visible_topic(topic_id, actor_role):
    topic = SyllabusTopicRepository.get_by_id(topic_id)
    if topic is None:
        raise ResourceNotFoundError("Syllabus topic not found.")
    unit, syllabus = _require_visible_unit(topic.unit_id, actor_role)
    return topic, unit, syllabus


def _require_draft_topic(topic):
    unit = SyllabusUnitRepository.get_by_id(topic.unit_id)
    if unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    _require_draft_unit(unit)
    return unit


def _validate_teaching_hours(hours):
    if hours is not None and hours < 0:
        raise ValueError("teaching_hours cannot be negative.")


def create_syllabus(curriculum_course_id, data):
    entry = _require_curriculum_course(curriculum_course_id)
    curriculum = _curriculum_for_course(entry)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "Syllabi can be added only to a DRAFT curriculum."
        )
    version = data.get("version")
    if version is None:
        version = SyllabusRepository.get_max_version(entry.id) + 1
    elif SyllabusRepository.get_by_version(entry.id, version) is not None:
        raise ResourceConflictError(
            "This syllabus version already exists for the curriculum course."
        )
    syllabus = Syllabus(
        curriculum_course_id=entry.id,
        title=data["title"].strip(),
        description=data.get("description"),
        objectives=data.get("objectives"),
        version=version,
        status="DRAFT",
    )
    return _persist(
        SyllabusRepository.create,
        syllabus,
        "This syllabus version already exists for the curriculum course.",
    )


def get_syllabus(syllabus_id, actor_role="ADMIN"):
    return _require_visible_syllabus(syllabus_id, actor_role)


def list_syllabi(curriculum_course_id, actor_role="ADMIN"):
    entry = _require_curriculum_course(curriculum_course_id)
    curriculum = _curriculum_for_course(entry)
    if actor_role != "ADMIN" and curriculum.status != "PUBLISHED":
        raise ResourceNotFoundError("Curriculum course not found.")
    syllabi = SyllabusRepository.list_by_curriculum_course(entry.id)
    if actor_role != "ADMIN":
        syllabi = [
            syllabus for syllabus in syllabi
            if syllabus.status == "PUBLISHED"
        ]
    return syllabi


def update_syllabus(syllabus_id, data):
    syllabus = _require_syllabus(syllabus_id)
    _require_draft_syllabus(syllabus)
    if "title" in data:
        syllabus.title = data["title"].strip()
    if "description" in data:
        syllabus.description = data["description"]
    if "objectives" in data:
        syllabus.objectives = data["objectives"]
    return _persist(
        SyllabusRepository.save,
        syllabus,
        "Syllabus could not be updated.",
    )


def delete_syllabus(syllabus_id):
    syllabus = _require_syllabus(syllabus_id)
    _require_draft_syllabus(syllabus)
    try:
        SyllabusRepository.delete(syllabus)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(
            "Syllabus could not be deleted while it is referenced."
        ) from exc


def publish_syllabus(syllabus_id):
    syllabus = _require_syllabus(syllabus_id)
    _require_draft_syllabus(syllabus)
    if not _syllabus_is_complete(syllabus):
        raise InvalidResourceStateError(
            "A syllabus requires at least one unit, topic, and learning "
            "outcome, with every topic and outcome mapped, before publishing."
        )
    existing_published = [
        item
        for item in SyllabusRepository.list_by_curriculum_course(
            syllabus.curriculum_course_id
        )
        if item.id != syllabus.id and item.status == "PUBLISHED"
    ]
    if existing_published:
        raise InvalidResourceStateError(
            "Archive the currently published syllabus before publishing "
            "another version."
        )
    syllabus.status = "PUBLISHED"
    return _persist(
        SyllabusRepository.save,
        syllabus,
        "Syllabus could not be published.",
    )


def archive_syllabus(syllabus_id):
    syllabus = _require_syllabus(syllabus_id)
    curriculum, _ = _curriculum_for_syllabus(syllabus)
    if curriculum.status != "DRAFT":
        raise InvalidResourceStateError(
            "A syllabus cannot be archived after its curriculum is published."
        )
    if syllabus.status != "PUBLISHED":
        raise InvalidResourceStateError(
            "Only PUBLISHED syllabi can be archived."
        )
    syllabus.status = "ARCHIVED"
    return _persist(
        SyllabusRepository.save,
        syllabus,
        "Syllabus could not be archived.",
    )


def create_syllabus_unit(syllabus_id, data):
    syllabus = _require_syllabus(syllabus_id)
    _require_draft_syllabus(syllabus)
    if SyllabusUnitRepository.get_by_unit_number(
        syllabus.id,
        data["unit_number"],
    ):
        raise ResourceConflictError(
            "Unit number already exists in this syllabus."
        )
    if SyllabusUnitRepository.get_by_sequence(
        syllabus.id,
        data["sequence_order"],
    ):
        raise ResourceConflictError(
            "Sequence position already exists in this syllabus."
        )
    _validate_teaching_hours(data.get("teaching_hours"))
    unit = SyllabusUnit(
        syllabus_id=syllabus.id,
        unit_number=data["unit_number"],
        title=data["title"].strip(),
        description=data.get("description"),
        sequence_order=data["sequence_order"],
        teaching_hours=data.get("teaching_hours"),
    )
    return _persist(
        SyllabusUnitRepository.create,
        unit,
        "Unit number or sequence position already exists in this syllabus.",
    )


def list_syllabus_units(syllabus_id, actor_role="ADMIN"):
    _require_visible_syllabus(syllabus_id, actor_role)
    return SyllabusUnitRepository.list_by_syllabus(syllabus_id)


def update_syllabus_unit(unit_id, data):
    unit = SyllabusUnitRepository.get_by_id(unit_id)
    if unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    _require_draft_unit(unit)
    number = data.get("unit_number", unit.unit_number)
    sequence = data.get("sequence_order", unit.sequence_order)
    existing_number = SyllabusUnitRepository.get_by_unit_number(
        unit.syllabus_id,
        number,
    )
    existing_sequence = SyllabusUnitRepository.get_by_sequence(
        unit.syllabus_id,
        sequence,
    )
    if existing_number is not None and existing_number.id != unit.id:
        raise ResourceConflictError(
            "Unit number already exists in this syllabus."
        )
    if existing_sequence is not None and existing_sequence.id != unit.id:
        raise ResourceConflictError(
            "Sequence position already exists in this syllabus."
        )
    hours = data.get("teaching_hours", unit.teaching_hours)
    _validate_teaching_hours(hours)
    unit.unit_number = number
    unit.sequence_order = sequence
    unit.teaching_hours = hours
    unit.title = data.get("title", unit.title).strip()
    unit.description = data.get("description", unit.description)
    return _persist(
        SyllabusUnitRepository.save,
        unit,
        "Unit number or sequence position already exists in this syllabus.",
    )


def delete_syllabus_unit(unit_id):
    unit = SyllabusUnitRepository.get_by_id(unit_id)
    if unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    _require_draft_unit(unit)
    try:
        SyllabusUnitRepository.delete(unit)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(
            "Syllabus unit could not be deleted while it is referenced."
        ) from exc


def create_syllabus_topic(unit_id, data):
    unit = SyllabusUnitRepository.get_by_id(unit_id)
    if unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    _require_draft_unit(unit)
    sequence = data["sequence_order"]
    if SyllabusTopicRepository.get_by_sequence(unit.id, sequence):
        raise ResourceConflictError(
            "Sequence position already exists in this unit."
        )
    _validate_teaching_hours(data.get("teaching_hours"))
    topic = SyllabusTopic(
        unit_id=unit.id,
        title=data["title"].strip(),
        description=data.get("description"),
        sequence_order=sequence,
        teaching_hours=data.get("teaching_hours"),
        reference_url=data.get("reference_url"),
    )
    return _persist(
        SyllabusTopicRepository.create,
        topic,
        "Sequence position already exists in this unit.",
    )


def list_syllabus_topics(unit_id, actor_role="ADMIN"):
    unit = SyllabusUnitRepository.get_by_id(unit_id)
    if unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    _require_visible_syllabus(unit.syllabus_id, actor_role)
    return SyllabusTopicRepository.list_by_unit(unit.id)


def update_syllabus_topic(topic_id, data):
    topic = SyllabusTopicRepository.get_by_id(topic_id)
    if topic is None:
        raise ResourceNotFoundError("Syllabus topic not found.")
    _require_draft_topic(topic)
    sequence = data.get("sequence_order", topic.sequence_order)
    existing = SyllabusTopicRepository.get_by_sequence(topic.unit_id, sequence)
    if existing is not None and existing.id != topic.id:
        raise ResourceConflictError(
            "Sequence position already exists in this unit."
        )
    hours = data.get("teaching_hours", topic.teaching_hours)
    _validate_teaching_hours(hours)
    topic.sequence_order = sequence
    topic.teaching_hours = hours
    topic.title = data.get("title", topic.title).strip()
    topic.description = data.get("description", topic.description)
    topic.reference_url = data.get("reference_url", topic.reference_url)
    return _persist(
        SyllabusTopicRepository.save,
        topic,
        "Sequence position already exists in this unit.",
    )


def delete_syllabus_topic(topic_id):
    topic = SyllabusTopicRepository.get_by_id(topic_id)
    if topic is None:
        raise ResourceNotFoundError("Syllabus topic not found.")
    _require_draft_topic(topic)
    try:
        SyllabusTopicRepository.delete(topic)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(
            "Syllabus topic could not be deleted while it is referenced."
        ) from exc


def create_learning_outcome(syllabus_id, data):
    syllabus = _require_syllabus(syllabus_id)
    _require_draft_syllabus(syllabus)
    code = data["outcome_code"].strip().upper()
    description = data["description"].strip()
    if not description:
        raise ValueError("Learning outcome description cannot be blank.")
    if LearningOutcomeRepository.get_by_code(syllabus.id, code):
        raise ResourceConflictError(
            "Outcome code already exists in this syllabus."
        )
    outcome = LearningOutcome(
        syllabus_id=syllabus.id,
        outcome_code=code,
        description=description,
        outcome_type=(
            data["outcome_type"].strip()
            if data.get("outcome_type")
            else None
        ),
    )
    return _persist(
        LearningOutcomeRepository.create,
        outcome,
        "Outcome code already exists in this syllabus.",
    )


def list_learning_outcomes(syllabus_id, actor_role="ADMIN"):
    _require_visible_syllabus(syllabus_id, actor_role)
    return LearningOutcomeRepository.list_by_syllabus(syllabus_id)


def update_learning_outcome(outcome_id, data):
    outcome = LearningOutcomeRepository.get_by_id(outcome_id)
    if outcome is None:
        raise ResourceNotFoundError("Learning outcome not found.")
    syllabus = _require_syllabus(outcome.syllabus_id)
    _require_draft_syllabus(syllabus)
    code = data.get("outcome_code", outcome.outcome_code).strip().upper()
    existing = LearningOutcomeRepository.get_by_code(syllabus.id, code)
    if existing is not None and existing.id != outcome.id:
        raise ResourceConflictError(
            "Outcome code already exists in this syllabus."
        )
    description = data.get("description", outcome.description).strip()
    if not description:
        raise ValueError("Learning outcome description cannot be blank.")
    outcome.outcome_code = code
    outcome.description = description
    if "outcome_type" in data:
        value = data["outcome_type"]
        outcome.outcome_type = value.strip() if value else None
    return _persist(
        LearningOutcomeRepository.save,
        outcome,
        "Outcome code already exists in this syllabus.",
    )


def delete_learning_outcome(outcome_id):
    outcome = LearningOutcomeRepository.get_by_id(outcome_id)
    if outcome is None:
        raise ResourceNotFoundError("Learning outcome not found.")
    syllabus = _require_syllabus(outcome.syllabus_id)
    _require_draft_syllabus(syllabus)
    try:
        LearningOutcomeRepository.delete(outcome)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(
            "Learning outcome could not be deleted while it is referenced."
        ) from exc


def create_topic_learning_outcome(topic_id, data):
    topic = SyllabusTopicRepository.get_by_id(topic_id)
    if topic is None:
        raise ResourceNotFoundError("Syllabus topic not found.")
    topic_unit = SyllabusUnitRepository.get_by_id(topic.unit_id)
    if topic_unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    topic_syllabus = _require_syllabus(topic_unit.syllabus_id)
    _require_draft_syllabus(topic_syllabus)
    outcome = LearningOutcomeRepository.get_by_id(
        data["learning_outcome_id"]
    )
    if outcome is None:
        raise ResourceNotFoundError("Learning outcome not found.")
    if outcome.syllabus_id != topic_syllabus.id:
        raise ValueError(
            "Topic and learning outcome must belong to the same syllabus."
        )
    if TopicLearningOutcomeRepository.get_by_topic_and_outcome(
        topic.id,
        outcome.id,
    ):
        raise ResourceConflictError(
            "This topic is already mapped to the learning outcome."
        )
    mapping = TopicLearningOutcome(
        topic_id=topic.id,
        learning_outcome_id=outcome.id,
    )
    return _persist(
        TopicLearningOutcomeRepository.create,
        mapping,
        "This topic/outcome mapping already exists.",
    )


def list_topic_learning_outcomes(topic_id, actor_role="ADMIN"):
    topic, _, _ = _require_visible_topic(topic_id, actor_role)
    return TopicLearningOutcomeRepository.list_by_topic(topic.id)


def delete_topic_learning_outcome(topic_id, outcome_id):
    topic = SyllabusTopicRepository.get_by_id(topic_id)
    if topic is None:
        raise ResourceNotFoundError("Syllabus topic not found.")
    unit = SyllabusUnitRepository.get_by_id(topic.unit_id)
    if unit is None:
        raise ResourceNotFoundError("Syllabus unit not found.")
    syllabus = _require_syllabus(unit.syllabus_id)
    _require_draft_syllabus(syllabus)
    mapping = TopicLearningOutcomeRepository.get_by_topic_and_outcome(
        topic.id,
        outcome_id,
    )
    if mapping is None:
        raise ResourceNotFoundError(
            "Topic learning outcome mapping not found."
        )
    try:
        TopicLearningOutcomeRepository.delete(mapping)
    except IntegrityError as exc:
        db.session.rollback()
        raise ResourceConflictError(
            "Topic learning outcome mapping could not be removed."
        ) from exc
