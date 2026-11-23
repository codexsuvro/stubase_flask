from flask_jwt_extended import get_jwt_identity
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.announcements.schemas import (
    AnnouncementCreateSchema,
    AnnouncementPaginatedResponseSchema,
    AnnouncementQuerySchema,
    AnnouncementResponseSchema,
    AnnouncementUpdateSchema,
)
from app.announcements.service import (
    AnnouncementError,
    AnnouncementConflictError,
    AnnouncementForbiddenError,
    AnnouncementNotFoundError,
    AnnouncementValidationError,
    archive_announcement,
    create_announcement,
    get_announcement_for_user,
    list_announcements_for_user,
    publish_announcement,
    update_announcement,
)
from app.auth.permissions import role_required


blp = Blueprint(
    "Announcements",
    __name__,
    url_prefix="/announcements",
    description="Global and course-offering announcements.",
)


def _handle_announcement_error(exc):
    if isinstance(exc, AnnouncementNotFoundError):
        abort(404, message=str(exc))
    if isinstance(exc, AnnouncementForbiddenError):
        abort(403, message=str(exc))
    if isinstance(exc, AnnouncementConflictError):
        abort(409, message=str(exc))
    if isinstance(exc, AnnouncementValidationError):
        abort(422, message=str(exc))
    raise exc


@blp.route("")
class AnnouncementCollectionResource(MethodView):

    @blp.doc(
        summary="Create a draft announcement",
        description=(
            "Administrators can create global or course announcements. "
            "Faculty can create announcements for their assigned offerings."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AnnouncementCreateSchema)
    @blp.response(201, AnnouncementResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, data):
        try:
            return create_announcement(data, get_jwt_identity())
        except AnnouncementError as exc:
            _handle_announcement_error(exc)

    @blp.doc(
        summary="List announcements visible to the authenticated user",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AnnouncementQuerySchema, location="query")
    @blp.response(200, AnnouncementPaginatedResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, query_args):
        try:
            return list_announcements_for_user(
                get_jwt_identity(),
                page=query_args["page"],
                per_page=query_args["per_page"],
                status=query_args.get("status"),
            )
        except AnnouncementError as exc:
            _handle_announcement_error(exc)


@blp.route("/<uuid:announcement_id>")
class AnnouncementDetailResource(MethodView):

    @blp.doc(
        summary="Get an announcement",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AnnouncementResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, announcement_id):
        try:
            return get_announcement_for_user(
                announcement_id,
                get_jwt_identity(),
            )
        except AnnouncementError as exc:
            _handle_announcement_error(exc)

    @blp.doc(
        summary="Update a draft announcement",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AnnouncementUpdateSchema)
    @blp.response(200, AnnouncementResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, announcement_id):
        try:
            return update_announcement(
                announcement_id,
                data,
                get_jwt_identity(),
            )
        except AnnouncementError as exc:
            _handle_announcement_error(exc)


@blp.route("/<uuid:announcement_id>/publish")
class PublishAnnouncementResource(MethodView):

    @blp.doc(
        summary="Publish an announcement and notify its audience",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AnnouncementResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, announcement_id):
        try:
            return publish_announcement(
                announcement_id,
                get_jwt_identity(),
            )
        except AnnouncementError as exc:
            _handle_announcement_error(exc)


@blp.route("/<uuid:announcement_id>/archive")
class ArchiveAnnouncementResource(MethodView):

    @blp.doc(
        summary="Archive an announcement",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AnnouncementResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, announcement_id):
        try:
            return archive_announcement(
                announcement_id,
                get_jwt_identity(),
            )
        except AnnouncementError as exc:
            _handle_announcement_error(exc)
