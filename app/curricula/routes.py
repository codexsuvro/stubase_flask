from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from flask_smorest import Blueprint, abort

from app.auth.permissions import role_required
from app.auth.repository import get_user_by_id
from app.curricula.schemas import (
    CurriculumCreateSchema,
    CurriculumCourseCreateSchema,
    CurriculumCourseResponseSchema,
    CurriculumPaginatedResponseSchema,
    CurriculumQuerySchema,
    CurriculumResponseSchema,
    CurriculumUpdateSchema,
    LearningOutcomeCreateSchema,
    LearningOutcomeResponseSchema,
    LearningOutcomeUpdateSchema,
    SyllabusCreateSchema,
    SyllabusResponseSchema,
    SyllabusTopicCreateSchema,
    SyllabusTopicResponseSchema,
    SyllabusTopicUpdateSchema,
    SyllabusUnitCreateSchema,
    SyllabusUnitResponseSchema,
    SyllabusUnitUpdateSchema,
    SyllabusUpdateSchema,
    TopicLearningOutcomeCreateSchema,
    TopicLearningOutcomeResponseSchema,
)
from app.curricula import service
from app.curricula.service import CurriculumModuleError


blp = Blueprint(
    "Curricula",
    __name__,
    description="Curriculum and syllabus management.",
)


def _actor_role():
    user = get_user_by_id(get_jwt_identity())
    if user is None or user.role is None:
        abort(401, message="Authenticated user or role was not found.")
    return user.role.role_name.strip().upper()


def _run(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except CurriculumModuleError as exc:
        abort(exc.status_code, message=str(exc))
    except ValueError as exc:
        abort(422, message=str(exc))


@blp.route("/curriculums")
class CurriculumCollectionResource(MethodView):
    @blp.doc(
        summary="Create a curriculum",
        description="Creates a DRAFT curriculum. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(CurriculumCreateSchema)
    @blp.response(201, CurriculumResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        return _run(service.create_curriculum, data)

    @blp.doc(
        summary="List curriculums",
        description=(
            "Returns paginated curriculums with optional department, "
            "academic-year, status, and code filters. Non-admin users see "
            "published curriculums only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(CurriculumQuerySchema, location="query")
    @blp.response(200, CurriculumPaginatedResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, query):
        return _run(
            service.list_curriculums,
            actor_role=_actor_role(),
            page=query["page"],
            per_page=query["per_page"],
            department_id=query.get("department_id"),
            academic_year_id=query.get("academic_year_id"),
            status=query.get("status"),
            curriculum_code=query.get("curriculum_code"),
        )


@blp.route("/curriculums/<uuid:curriculum_id>")
class CurriculumDetailResource(MethodView):
    @blp.doc(
        summary="Get curriculum details",
        description="Non-admin users can view published curriculums only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, CurriculumResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, curriculum_id):
        return _run(
            service.get_curriculum,
            curriculum_id,
            actor_role=_actor_role(),
        )

    @blp.doc(
        summary="Update a draft curriculum",
        description="Only DRAFT curriculums can be updated. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(CurriculumUpdateSchema)
    @blp.response(200, CurriculumResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, curriculum_id):
        return _run(service.update_curriculum, curriculum_id, data)

    @blp.doc(
        summary="Delete a draft curriculum",
        description="Only eligible DRAFT curriculums can be deleted. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN")
    def delete(self, curriculum_id):
        _run(service.delete_curriculum, curriculum_id)
        return "", 204


@blp.route("/curriculums/<uuid:curriculum_id>/publish")
class CurriculumPublishResource(MethodView):
    @blp.doc(
        summary="Publish a curriculum",
        description=(
            "Publishes a DRAFT curriculum after every assigned course has "
            "a complete published syllabus. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, CurriculumResponseSchema)
    @role_required("ADMIN")
    def post(self, curriculum_id):
        return _run(service.publish_curriculum, curriculum_id)


@blp.route("/curriculums/<uuid:curriculum_id>/archive")
class CurriculumArchiveResource(MethodView):
    @blp.doc(
        summary="Archive a curriculum",
        description="Archives a PUBLISHED curriculum. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, CurriculumResponseSchema)
    @role_required("ADMIN")
    def post(self, curriculum_id):
        return _run(service.archive_curriculum, curriculum_id)


@blp.route("/curriculums/<uuid:curriculum_id>/courses")
class CurriculumCourseCollectionResource(MethodView):
    @blp.doc(
        summary="Add a course to a curriculum",
        description="Adds an eligible course to a DRAFT curriculum. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(CurriculumCourseCreateSchema)
    @blp.response(201, CurriculumCourseResponseSchema)
    @role_required("ADMIN")
    def post(self, data, curriculum_id):
        return _run(
            service.create_curriculum_course,
            curriculum_id,
            data,
        )

    @blp.doc(
        summary="List curriculum courses",
        description="Non-admin users can list courses in published curriculums only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, CurriculumCourseResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, curriculum_id):
        return _run(
            service.list_curriculum_courses,
            curriculum_id,
            actor_role=_actor_role(),
        )


@blp.route(
    "/curriculums/<uuid:curriculum_id>/courses/<uuid:curriculum_course_id>"
)
class CurriculumCourseDetailResource(MethodView):
    @blp.doc(
        summary="Remove a course from a curriculum",
        description="Removes a course from an eligible DRAFT curriculum. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN")
    def delete(self, curriculum_id, curriculum_course_id):
        _run(
            service.remove_curriculum_course,
            curriculum_id,
            curriculum_course_id,
        )
        return "", 204


@blp.route(
    "/curriculum-courses/<uuid:curriculum_course_id>/syllabi"
)
class SyllabusCollectionResource(MethodView):
    @blp.doc(
        summary="Create a syllabus version",
        description=(
            "Creates a DRAFT syllabus for a course in a DRAFT curriculum. "
            "Version is assigned automatically when omitted. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SyllabusCreateSchema)
    @blp.response(201, SyllabusResponseSchema)
    @role_required("ADMIN")
    def post(self, data, curriculum_course_id):
        return _run(
            service.create_syllabus,
            curriculum_course_id,
            data,
        )

    @blp.doc(
        summary="List syllabus versions",
        description="Non-admin users see published versions in published curriculums only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SyllabusResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, curriculum_course_id):
        return _run(
            service.list_syllabi,
            curriculum_course_id,
            actor_role=_actor_role(),
        )


@blp.route("/syllabi/<uuid:syllabus_id>")
class SyllabusDetailResource(MethodView):
    @blp.doc(
        summary="Get syllabus details",
        description="Non-admin users can view published syllabi only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SyllabusResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, syllabus_id):
        return _run(
            service.get_syllabus,
            syllabus_id,
            actor_role=_actor_role(),
        )

    @blp.doc(
        summary="Update a draft syllabus",
        description="Only DRAFT syllabi in DRAFT curriculums can be updated. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SyllabusUpdateSchema)
    @blp.response(200, SyllabusResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, syllabus_id):
        return _run(service.update_syllabus, syllabus_id, data)

    @blp.doc(
        summary="Delete a draft syllabus",
        description="Only DRAFT syllabi in DRAFT curriculums can be deleted. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN")
    def delete(self, syllabus_id):
        _run(service.delete_syllabus, syllabus_id)
        return "", 204


@blp.route("/syllabi/<uuid:syllabus_id>/publish")
class SyllabusPublishResource(MethodView):
    @blp.doc(
        summary="Publish a syllabus",
        description="Publishes a complete DRAFT syllabus before its curriculum is published. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SyllabusResponseSchema)
    @role_required("ADMIN")
    def post(self, syllabus_id):
        return _run(service.publish_syllabus, syllabus_id)


@blp.route("/syllabi/<uuid:syllabus_id>/archive")
class SyllabusArchiveResource(MethodView):
    @blp.doc(
        summary="Archive a syllabus",
        description="Archives a PUBLISHED syllabus while its curriculum remains DRAFT. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SyllabusResponseSchema)
    @role_required("ADMIN")
    def post(self, syllabus_id):
        return _run(service.archive_syllabus, syllabus_id)


@blp.route("/syllabi/<uuid:syllabus_id>/units")
class SyllabusUnitCollectionResource(MethodView):
    @blp.doc(
        summary="Create a syllabus unit",
        description="Creates a unit in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SyllabusUnitCreateSchema)
    @blp.response(201, SyllabusUnitResponseSchema)
    @role_required("ADMIN")
    def post(self, data, syllabus_id):
        return _run(service.create_syllabus_unit, syllabus_id, data)

    @blp.doc(
        summary="List syllabus units",
        description="Non-admin users can view units in published syllabi only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SyllabusUnitResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, syllabus_id):
        return _run(
            service.list_syllabus_units,
            syllabus_id,
            actor_role=_actor_role(),
        )


@blp.route("/syllabus-units/<uuid:unit_id>")
class SyllabusUnitDetailResource(MethodView):
    @blp.doc(
        summary="Update a syllabus unit",
        description="Updates a unit in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SyllabusUnitUpdateSchema)
    @blp.response(200, SyllabusUnitResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, unit_id):
        return _run(service.update_syllabus_unit, unit_id, data)

    @blp.doc(
        summary="Delete a syllabus unit",
        description="Deletes a unit in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN")
    def delete(self, unit_id):
        _run(service.delete_syllabus_unit, unit_id)
        return "", 204


@blp.route("/syllabus-units/<uuid:unit_id>/topics")
class SyllabusTopicCollectionResource(MethodView):
    @blp.doc(
        summary="Create a syllabus topic",
        description="Creates a topic under a unit in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SyllabusTopicCreateSchema)
    @blp.response(201, SyllabusTopicResponseSchema)
    @role_required("ADMIN")
    def post(self, data, unit_id):
        return _run(service.create_syllabus_topic, unit_id, data)

    @blp.doc(
        summary="List syllabus topics",
        description="Non-admin users can view topics in published syllabi only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SyllabusTopicResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, unit_id):
        return _run(
            service.list_syllabus_topics,
            unit_id,
            actor_role=_actor_role(),
        )


@blp.route("/syllabus-topics/<uuid:topic_id>")
class SyllabusTopicDetailResource(MethodView):
    @blp.doc(
        summary="Update a syllabus topic",
        description="Updates a topic in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SyllabusTopicUpdateSchema)
    @blp.response(200, SyllabusTopicResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, topic_id):
        return _run(service.update_syllabus_topic, topic_id, data)

    @blp.doc(
        summary="Delete a syllabus topic",
        description="Deletes a topic in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN")
    def delete(self, topic_id):
        _run(service.delete_syllabus_topic, topic_id)
        return "", 204


@blp.route("/syllabi/<uuid:syllabus_id>/learning-outcomes")
class LearningOutcomeCollectionResource(MethodView):
    @blp.doc(
        summary="Create a learning outcome",
        description="Creates an outcome in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(LearningOutcomeCreateSchema)
    @blp.response(201, LearningOutcomeResponseSchema)
    @role_required("ADMIN")
    def post(self, data, syllabus_id):
        return _run(service.create_learning_outcome, syllabus_id, data)

    @blp.doc(
        summary="List learning outcomes",
        description="Non-admin users can view outcomes in published syllabi only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, LearningOutcomeResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, syllabus_id):
        return _run(
            service.list_learning_outcomes,
            syllabus_id,
            actor_role=_actor_role(),
        )


@blp.route("/learning-outcomes/<uuid:outcome_id>")
class LearningOutcomeDetailResource(MethodView):
    @blp.doc(
        summary="Update a learning outcome",
        description="Updates an outcome in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(LearningOutcomeUpdateSchema)
    @blp.response(200, LearningOutcomeResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, outcome_id):
        return _run(service.update_learning_outcome, outcome_id, data)

    @blp.doc(
        summary="Delete a learning outcome",
        description="Deletes an outcome in a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN")
    def delete(self, outcome_id):
        _run(service.delete_learning_outcome, outcome_id)
        return "", 204


@blp.route("/syllabus-topics/<uuid:topic_id>/learning-outcomes")
class TopicLearningOutcomeCollectionResource(MethodView):
    @blp.doc(
        summary="Map a topic to a learning outcome",
        description=(
            "The topic and outcome must belong to the same DRAFT syllabus. "
            "ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(TopicLearningOutcomeCreateSchema)
    @blp.response(201, TopicLearningOutcomeResponseSchema)
    @role_required("ADMIN")
    def post(self, data, topic_id):
        return _run(service.create_topic_learning_outcome, topic_id, data)

    @blp.doc(
        summary="List topic learning-outcome mappings",
        description="Non-admin users can view mappings in published syllabi only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, TopicLearningOutcomeResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, topic_id):
        return _run(
            service.list_topic_learning_outcomes,
            topic_id,
            actor_role=_actor_role(),
        )


@blp.route(
    "/syllabus-topics/<uuid:topic_id>/learning-outcomes/<uuid:outcome_id>"
)
class TopicLearningOutcomeDetailResource(MethodView):
    @blp.doc(
        summary="Remove a topic learning-outcome mapping",
        description="Removes a mapping from a DRAFT syllabus. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN")
    def delete(self, topic_id, outcome_id):
        _run(
            service.delete_topic_learning_outcome,
            topic_id,
            outcome_id,
        )
        return "", 204
