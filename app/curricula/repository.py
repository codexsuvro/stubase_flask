from sqlalchemy import select, func

from app.extensions import db
from app.curricula.models import (
    Curriculum,
    CurriculumCourse,
    LearningOutcome,
    Syllabus,
    SyllabusTopic,
    SyllabusUnit,
    TopicLearningOutcome,
)
from app.models.semester import Semester


def _commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _save(instance):
    db.session.add(instance)
    _commit()
    db.session.refresh(instance)
    return instance


def _delete(instance):
    db.session.delete(instance)
    _commit()


class CurriculumRepository:
    @staticmethod
    def create(curriculum):
        return _save(curriculum)

    @staticmethod
    def get_by_id(curriculum_id):
        return db.session.get(Curriculum, curriculum_id)

    @staticmethod
    def get_by_unique_key(
        department_id,
        academic_year_id,
        curriculum_code,
        version,
    ):
        statement = select(Curriculum).where(
            Curriculum.department_id == department_id,
            Curriculum.academic_year_id == academic_year_id,
            Curriculum.curriculum_code == curriculum_code,
            Curriculum.version == version,
        )
        return db.session.scalar(statement)

    @staticmethod
    def list_paginated(
        page,
        per_page,
        department_id=None,
        academic_year_id=None,
        status=None,
        curriculum_code=None,
        published_only=False,
    ):
        statement = select(Curriculum)
        if department_id is not None:
            statement = statement.where(
                Curriculum.department_id == department_id
            )
        if academic_year_id is not None:
            statement = statement.where(
                Curriculum.academic_year_id == academic_year_id
            )
        if status is not None:
            statement = statement.where(Curriculum.status == status)
        if curriculum_code is not None:
            statement = statement.where(
                Curriculum.curriculum_code.ilike(
                    f"%{curriculum_code}%"
                )
            )
        if published_only:
            statement = statement.where(
                Curriculum.status == "PUBLISHED"
            )

        total_records = db.session.scalar(
            select(func.count()).select_from(
                statement.order_by(None).subquery()
            )
        ) or 0
        items = db.session.scalars(
            statement
            .order_by(Curriculum.created_at.desc(), Curriculum.id.asc())
            .limit(per_page)
            .offset((page - 1) * per_page)
        ).all()
        total_pages = (
            (total_records + per_page - 1) // per_page
            if total_records
            else 0
        )
        return {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }

    @staticmethod
    def save(curriculum):
        return _save(curriculum)

    @staticmethod
    def delete(curriculum):
        _delete(curriculum)


class CurriculumCourseRepository:
    @staticmethod
    def create(curriculum_course):
        return _save(curriculum_course)

    @staticmethod
    def get_by_id(curriculum_course_id):
        return db.session.get(CurriculumCourse, curriculum_course_id)

    @staticmethod
    def get_by_course(curriculum_id, course_id):
        statement = select(CurriculumCourse).where(
            CurriculumCourse.curriculum_id == curriculum_id,
            CurriculumCourse.course_id == course_id,
        )
        return db.session.scalar(statement)

    @staticmethod
    def get_by_sequence(curriculum_id, semester_id, sequence_order):
        statement = select(CurriculumCourse).where(
            CurriculumCourse.curriculum_id == curriculum_id,
            CurriculumCourse.semester_id == semester_id,
            CurriculumCourse.sequence_order == sequence_order,
        )
        return db.session.scalar(statement)

    @staticmethod
    def list_by_curriculum(curriculum_id):
        statement = (
            select(CurriculumCourse)
            .join(CurriculumCourse.semester)
            .where(CurriculumCourse.curriculum_id == curriculum_id)
            .order_by(
                Semester.semester_number.asc(),
                CurriculumCourse.sequence_order.asc(),
                CurriculumCourse.id.asc(),
            )
        )
        return db.session.scalars(statement).all()

    @staticmethod
    def delete(curriculum_course):
        _delete(curriculum_course)


class SyllabusRepository:
    @staticmethod
    def create(syllabus):
        return _save(syllabus)

    @staticmethod
    def get_by_id(syllabus_id):
        return db.session.get(Syllabus, syllabus_id)

    @staticmethod
    def get_by_version(curriculum_course_id, version):
        statement = select(Syllabus).where(
            Syllabus.curriculum_course_id == curriculum_course_id,
            Syllabus.version == version,
        )
        return db.session.scalar(statement)

    @staticmethod
    def get_max_version(curriculum_course_id):
        statement = select(func.max(Syllabus.version)).where(
            Syllabus.curriculum_course_id == curriculum_course_id
        )
        return db.session.scalar(statement) or 0

    @staticmethod
    def list_by_curriculum_course(curriculum_course_id):
        statement = (
            select(Syllabus)
            .where(Syllabus.curriculum_course_id == curriculum_course_id)
            .order_by(Syllabus.version.desc(), Syllabus.id.asc())
        )
        return db.session.scalars(statement).all()

    @staticmethod
    def save(syllabus):
        return _save(syllabus)

    @staticmethod
    def delete(syllabus):
        _delete(syllabus)


class SyllabusUnitRepository:
    @staticmethod
    def create(unit):
        return _save(unit)

    @staticmethod
    def get_by_id(unit_id):
        return db.session.get(SyllabusUnit, unit_id)

    @staticmethod
    def get_by_unit_number(syllabus_id, unit_number):
        statement = select(SyllabusUnit).where(
            SyllabusUnit.syllabus_id == syllabus_id,
            SyllabusUnit.unit_number == unit_number,
        )
        return db.session.scalar(statement)

    @staticmethod
    def get_by_sequence(syllabus_id, sequence_order):
        statement = select(SyllabusUnit).where(
            SyllabusUnit.syllabus_id == syllabus_id,
            SyllabusUnit.sequence_order == sequence_order,
        )
        return db.session.scalar(statement)

    @staticmethod
    def list_by_syllabus(syllabus_id):
        statement = (
            select(SyllabusUnit)
            .where(SyllabusUnit.syllabus_id == syllabus_id)
            .order_by(SyllabusUnit.sequence_order.asc(), SyllabusUnit.id.asc())
        )
        return db.session.scalars(statement).all()

    @staticmethod
    def save(unit):
        return _save(unit)

    @staticmethod
    def delete(unit):
        _delete(unit)


class SyllabusTopicRepository:
    @staticmethod
    def create(topic):
        return _save(topic)

    @staticmethod
    def get_by_id(topic_id):
        return db.session.get(SyllabusTopic, topic_id)

    @staticmethod
    def get_by_sequence(unit_id, sequence_order):
        statement = select(SyllabusTopic).where(
            SyllabusTopic.unit_id == unit_id,
            SyllabusTopic.sequence_order == sequence_order,
        )
        return db.session.scalar(statement)

    @staticmethod
    def list_by_unit(unit_id):
        statement = (
            select(SyllabusTopic)
            .where(SyllabusTopic.unit_id == unit_id)
            .order_by(SyllabusTopic.sequence_order.asc(), SyllabusTopic.id.asc())
        )
        return db.session.scalars(statement).all()

    @staticmethod
    def save(topic):
        return _save(topic)

    @staticmethod
    def delete(topic):
        _delete(topic)


class LearningOutcomeRepository:
    @staticmethod
    def create(outcome):
        return _save(outcome)

    @staticmethod
    def get_by_id(outcome_id):
        return db.session.get(LearningOutcome, outcome_id)

    @staticmethod
    def get_by_code(syllabus_id, outcome_code):
        statement = select(LearningOutcome).where(
            LearningOutcome.syllabus_id == syllabus_id,
            LearningOutcome.outcome_code == outcome_code,
        )
        return db.session.scalar(statement)

    @staticmethod
    def list_by_syllabus(syllabus_id):
        statement = (
            select(LearningOutcome)
            .where(LearningOutcome.syllabus_id == syllabus_id)
            .order_by(LearningOutcome.outcome_code.asc(), LearningOutcome.id.asc())
        )
        return db.session.scalars(statement).all()

    @staticmethod
    def save(outcome):
        return _save(outcome)

    @staticmethod
    def delete(outcome):
        _delete(outcome)


class TopicLearningOutcomeRepository:
    @staticmethod
    def create(mapping):
        return _save(mapping)

    @staticmethod
    def get_by_topic_and_outcome(topic_id, learning_outcome_id):
        statement = select(TopicLearningOutcome).where(
            TopicLearningOutcome.topic_id == topic_id,
            TopicLearningOutcome.learning_outcome_id == learning_outcome_id,
        )
        return db.session.scalar(statement)

    @staticmethod
    def list_by_topic(topic_id):
        statement = (
            select(TopicLearningOutcome)
            .where(TopicLearningOutcome.topic_id == topic_id)
            .order_by(
                TopicLearningOutcome.created_at.asc(),
                TopicLearningOutcome.id.asc(),
            )
        )
        return db.session.scalars(statement).all()

    @staticmethod
    def delete(mapping):
        _delete(mapping)
