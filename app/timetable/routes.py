from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity

from app.auth.permissions import role_required
from app.timetable.schemas import (
    ClassroomCreateSchema,
    ClassroomUpdateSchema,
    ClassroomResponseSchema,
    TimetableSlotCreateSchema,
    TimetableSlotUpdateSchema,
    TimetableSlotFilterSchema,
    TimetableSlotResponseSchema,
)
from app.timetable.service import (
    create_classroom,
    get_classroom,
    get_all_classrooms,
    update_classroom,
    create_timetable_slot,
    get_timetable_slot,
    get_all_timetable_slots,
    update_timetable_slot,
    cancel_timetable_slot,
    TimetableValidationError,
    TimetableConflictError,
)


blp = Blueprint(
    "Timetable",
    __name__,
    url_prefix="/",
    description="Classroom and timetable management.",
)


@blp.route("/classrooms")
class ClassroomCollectionResource(MethodView):

    @blp.doc(
        summary="Create a classroom",
        description="ADMIN only. Registers a classroom or laboratory.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ClassroomCreateSchema)
    @blp.response(201, ClassroomResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_classroom(data)
        except TimetableConflictError as exc:
            abort(409, message=str(exc))
        except TimetableValidationError as exc:
            abort(422, message=str(exc))

    @blp.doc(
        summary="List classrooms",
        description="ADMIN only. Supports filtering by classroom status.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ClassroomResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        from flask import request

        status = request.args.get("status")

        if status and status not in {"ACTIVE", "INACTIVE"}:
            abort(422, message="Invalid classroom status.")

        return get_all_classrooms(status=status)


@blp.route("/classrooms/<uuid:classroom_id>")
class ClassroomDetailResource(MethodView):

    @blp.doc(
        summary="Get classroom details",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ClassroomResponseSchema)
    @role_required("ADMIN")
    def get(self, classroom_id):
        try:
            return get_classroom(classroom_id)
        except Exception as exc:
            if exc.__class__.__name__ == "NotFound":
                abort(404, message=str(exc))
            raise

    @blp.doc(
        summary="Update classroom",
        description="ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ClassroomUpdateSchema)
    @blp.response(200, ClassroomResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, classroom_id):
        try:
            return update_classroom(classroom_id, data)
        except TimetableConflictError as exc:
            abort(409, message=str(exc))
        except TimetableValidationError as exc:
            abort(422, message=str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == "NotFound":
                abort(404, message=str(exc))
            raise


@blp.route("/timetable/slots")
class TimetableSlotCollectionResource(MethodView):

    @blp.doc(
        summary="Create a timetable slot",
        description=(
            "ADMIN only. Creates a weekly recurring timetable slot. "
            "Faculty is inherited from the selected Course Offering."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(TimetableSlotCreateSchema)
    @blp.response(201, TimetableSlotResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_timetable_slot(
                data,
                user_id=get_jwt_identity(),
            )
        except TimetableConflictError as exc:
            abort(409, message=str(exc))
        except TimetableValidationError as exc:
            abort(422, message=str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == "NotFound":
                abort(404, message=str(exc))
            raise

    @blp.doc(
        summary="List timetable slots",
        description=(
            "ADMIN can filter all slots. FACULTY can view only "
            "their own assigned timetable."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        TimetableSlotFilterSchema,
        location="query",
    )
    @blp.response(200, TimetableSlotResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY")
    def get(self, query_args):
        user_id = get_jwt_identity()

        from app.auth.repository import get_user_by_id
        user = get_user_by_id(user_id)
        role_name = user.role.role_name.upper()

        if role_name == "FACULTY":
            query_args.pop("faculty_id", None)

        return get_all_timetable_slots(
            query_args,
            user_id=user_id if role_name == "FACULTY" else None,
        )


@blp.route("/timetable/slots/<uuid:slot_id>")
class TimetableSlotDetailResource(MethodView):

    @blp.doc(
        summary="Get timetable slot",
        description=(
            "ADMIN can view any slot. FACULTY can view only "
            "their own assigned slot."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, TimetableSlotResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, slot_id):
        from app.auth.repository import get_user_by_id

        user = get_user_by_id(get_jwt_identity())
        role_name = user.role.role_name.upper()

        try:
            return get_timetable_slot(
                slot_id,
                user_id=(
                    get_jwt_identity()
                    if role_name == "FACULTY"
                    else None
                ),
            )
        except Exception as exc:
            if exc.__class__.__name__ == "NotFound":
                abort(404, message=str(exc))
            if exc.__class__.__name__ == "Forbidden":
                abort(403, message=str(exc))
            raise

    @blp.doc(
        summary="Update timetable slot",
        description="ADMIN only. Updates an existing active timetable slot.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(TimetableSlotUpdateSchema)
    @blp.response(200, TimetableSlotResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, slot_id):
        try:
            return update_timetable_slot(slot_id, data)
        except TimetableConflictError as exc:
            abort(409, message=str(exc))
        except TimetableValidationError as exc:
            abort(422, message=str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == "NotFound":
                abort(404, message=str(exc))
            raise


@blp.route("/timetable/slots/<uuid:slot_id>/cancel")
class TimetableSlotCancelResource(MethodView):

    @blp.doc(
        summary="Cancel timetable slot",
        description="ADMIN only. Cancels a slot without deleting its history.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, TimetableSlotResponseSchema)
    @role_required("ADMIN")
    def post(self, slot_id):
        try:
            return cancel_timetable_slot(slot_id)
        except TimetableValidationError as exc:
            abort(409, message=str(exc))
        except Exception as exc:
            if exc.__class__.__name__ == "NotFound":
                abort(404, message=str(exc))
            raise
