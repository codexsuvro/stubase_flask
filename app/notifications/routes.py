from flask_jwt_extended import get_jwt_identity
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.auth.permissions import role_required
from app.notifications.schemas import (
    MarkAllNotificationsReadSchema,
    NotificationPaginatedResponseSchema,
    NotificationQuerySchema,
    NotificationResponseSchema,
    UnreadNotificationCountSchema,
)
from app.notifications.service import (
    NotificationNotFoundError,
    get_my_unread_notification_count,
    list_my_notifications,
    mark_all_my_notifications_read,
    mark_notification_read,
)


blp = Blueprint(
    "Notifications",
    __name__,
    url_prefix="/notifications",
    description="User notification inbox and delivery status.",
)


@blp.route("/me")
class MyNotificationsResource(MethodView):

    @blp.doc(
        summary="List notifications for the authenticated user",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(NotificationQuerySchema, location="query")
    @blp.response(200, NotificationPaginatedResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, query_args):
        return list_my_notifications(
            get_jwt_identity(),
            page=query_args["page"],
            per_page=query_args["per_page"],
            unread_only=query_args["unread_only"],
        )


@blp.route("/me/unread-count")
class MyUnreadNotificationCountResource(MethodView):

    @blp.doc(
        summary="Get the authenticated user's unread notification count",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, UnreadNotificationCountSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self):
        return get_my_unread_notification_count(get_jwt_identity())


@blp.route("/me/read-all")
class MarkAllNotificationsReadResource(MethodView):

    @blp.doc(
        summary="Mark all of the authenticated user's notifications as read",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, MarkAllNotificationsReadSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def patch(self):
        return mark_all_my_notifications_read(get_jwt_identity())


@blp.route("/<uuid:notification_id>/read")
class MarkNotificationReadResource(MethodView):

    @blp.doc(
        summary="Mark one of the authenticated user's notifications as read",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, NotificationResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def patch(self, notification_id):
        try:
            return mark_notification_read(
                notification_id,
                get_jwt_identity(),
            )
        except NotificationNotFoundError as exc:
            abort(404, message=str(exc))
