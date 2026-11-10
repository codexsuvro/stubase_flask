from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.course_offerings.schemas import (
    CourseOfferingCreateSchema, CourseOfferingUpdateSchema,
    CourseOfferingStatusSchema, CourseOfferingResponseSchema,
)
from app.course_offerings.service import (
    create_offering, get_offering, get_all_offerings, update_offering,
    update_offering_status, CourseOfferingNotFoundError, CourseNotFoundError,
    SemesterNotFoundError, FacultyNotFoundError, CourseOfferingConflictError,
    InvalidCourseOfferingError,
)

blp = Blueprint("Course Offerings", __name__, url_prefix="/course-offerings",
                description="Course offering management.")


def handle_error(exc):
    if isinstance(exc, (CourseOfferingNotFoundError, CourseNotFoundError,
                        SemesterNotFoundError, FacultyNotFoundError)):
        abort(404, message=str(exc))
    if isinstance(exc, (CourseOfferingConflictError, InvalidCourseOfferingError)):
        abort(409, message=str(exc))
    if isinstance(exc, ValueError):
        abort(400, message=str(exc))
    raise exc


@blp.route("")
class CourseOfferingCollectionResource(MethodView):
    @blp.doc(summary="Create a course offering", security=[{"bearerAuth": []}])
    @blp.arguments(CourseOfferingCreateSchema)
    @blp.response(201, CourseOfferingResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_offering(data)
        except Exception as exc:
            handle_error(exc)

    @blp.doc(summary="List course offerings", security=[{"bearerAuth": []}])
    @blp.response(200, CourseOfferingResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self, **kwargs):
        from flask import request
        from marshmallow import ValidationError
        from uuid import UUID
        filters = {}
        for key in ("semester_id", "course_id", "faculty_id"):
            value = request.args.get(key)
            if value:
                try: filters[key] = UUID(value)
                except ValueError: abort(400, message=f"Invalid {key} UUID.")
        status = request.args.get("status")
        if status:
            if status not in {"DRAFT", "OPEN", "CLOSED", "CANCELLED"}:
                abort(400, message="Invalid offering status filter.")
            filters["status"] = status
        return get_all_offerings(filters)


@blp.route("/<uuid:offering_id>")
class CourseOfferingDetailResource(MethodView):
    @blp.doc(summary="Get a course offering", security=[{"bearerAuth": []}])
    @blp.response(200, CourseOfferingResponseSchema)
    @role_required("ADMIN")
    def get(self, offering_id):
        try: return get_offering(offering_id)
        except Exception as exc: handle_error(exc)

    @blp.doc(summary="Update a course offering", security=[{"bearerAuth": []}])
    @blp.arguments(CourseOfferingUpdateSchema)
    @blp.response(200, CourseOfferingResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, offering_id):
        try: return update_offering(offering_id, data)
        except Exception as exc: handle_error(exc)


@blp.route("/<uuid:offering_id>/status")
class CourseOfferingStatusResource(MethodView):
    @blp.doc(summary="Update course offering status", security=[{"bearerAuth": []}])
    @blp.arguments(CourseOfferingStatusSchema)
    @blp.response(200, CourseOfferingResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, offering_id):
        try: return update_offering_status(offering_id, data["status"])
        except Exception as exc: handle_error(exc)
