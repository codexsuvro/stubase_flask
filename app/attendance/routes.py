from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.attendance.schemas import (
    AttendanceCreateSchema,
    AttendanceResponseSchema,
    AttendanceSummarySchema,
    AttendanceUpdateSchema,
    AttendanceAuditResponseSchema,
    AttendanceShortageSchema,
)
from app.attendance.repository import list_attendance
from app.attendance.service import (
    create_attendance,
    EnrollmentNotFoundError,
    DuplicateAttendanceError,
    AttendanceNotFoundError,
    AttendancePermissionError,
    update_attendance,
    get_attendance_history,
    get_attendance_shortage,
    get_attendance_for_user,
    get_enrollment_attendance_for_user,
    get_attendance_summary_for_user,
)

from flask import request
from flask_jwt_extended import get_jwt_identity


blp = Blueprint(
    "Attendance",
    __name__,
    url_prefix="/attendance",
    description="Student attendance management.",
)


@blp.route("")
class AttendanceCollectionResource(MethodView):

    
    @blp.doc(
        summary="Record student attendance",
        description=(
            "ADMIN can record attendance for all courses. "
            "FACULTY can record attendance only for assigned courses."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AttendanceCreateSchema)
    @blp.response(201, AttendanceResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, data):
        try:
            return create_attendance(
                data,
                user_id=get_jwt_identity(),
            )
        except EnrollmentNotFoundError as exc:
            abort(404, message=str(exc))
        except DuplicateAttendanceError as exc:
            abort(409, message=str(exc))
        except AttendancePermissionError as exc:
            abort(403, message=str(exc))


    @blp.doc(
        summary="List all attendance records",
        description="ADMIN only. Returns all recorded attendance.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AttendanceResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        return list_attendance()


@blp.route("/<uuid:attendance_id>")
class AttendanceDetailResource(MethodView):

    @blp.doc(
        summary="Get attendance by UUID",
        description="ADMIN only. Returns one attendance record.",
        security=[{"bearerAuth": []}],
    )
    
    @blp.response(200, AttendanceResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, attendance_id):
        try:
            return get_attendance_for_user(
                attendance_id,
                get_jwt_identity(),
            )
        except AttendanceNotFoundError as exc:
            abort(404, message=str(exc))
        except AttendancePermissionError as exc:
            abort(403, message=str(exc))
    
    @blp.doc(
        summary="Update attendance",
        description=(
            "ADMIN only. Corrects attendance status or remarks. "
            "Every actual change is recorded in the audit history."
        ),
        security=[{"bearerAuth": []}],
    )
    
    @blp.arguments(AttendanceUpdateSchema)
    @blp.response(200, AttendanceResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, attendance_id):
        try:
            return update_attendance(
                attendance_id=attendance_id,
                data=data,
                changed_by_user_id=get_jwt_identity(),
            )
        except AttendanceNotFoundError as exc:
            abort(404, message=str(exc))
        except AttendancePermissionError as exc:
            abort(403, message=str(exc))


@blp.route("/enrollment/<uuid:enrollment_id>")
class EnrollmentAttendanceResource(MethodView):

    @blp.doc(
        summary="List attendance by enrollment",
        description=(
            "ADMIN only. Returns all attendance records "
            "for a specific enrollment."
        ),
        security=[{"bearerAuth": []}],
    )
    
    @blp.response(200, AttendanceResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY")
    def get(self, enrollment_id):
        try:
            return get_enrollment_attendance_for_user(
                enrollment_id,
                get_jwt_identity(),
            )
        except EnrollmentNotFoundError as exc:
            abort(404, message=str(exc))
        except AttendancePermissionError as exc:
            abort(403, message=str(exc))


@blp.route("/enrollment/<uuid:enrollment_id>/summary")
class AttendanceSummaryResource(MethodView):

    @blp.doc(
        summary="Get attendance summary",
        description=(
            "ADMIN only. Calculates total recorded classes, "
            "present, absent, late, and attendance percentage."
        ),
        security=[{"bearerAuth": []}],
    )
    
    @blp.response(200, AttendanceSummarySchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, enrollment_id):
        try:
            return get_attendance_summary_for_user(
                enrollment_id,
                get_jwt_identity(),
            )
        except EnrollmentNotFoundError as exc:
            abort(404, message=str(exc))
        except AttendancePermissionError as exc:
            abort(403, message=str(exc))
    

@blp.route("/<uuid:attendance_id>/history")
class AttendanceHistoryResource(MethodView):

    @blp.doc(
        summary="Get attendance correction history",
        description="ADMIN only. Returns all changes made to an attendance record.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AttendanceAuditResponseSchema(many=True))
    @role_required("ADMIN", "FACULTY")
    def get(self, attendance_id):
        try:
            return get_attendance_history(
                attendance_id,
                get_jwt_identity(),
            )
        except AttendanceNotFoundError as exc:
            abort(404, message=str(exc))
        except AttendancePermissionError as exc:
            abort(403, message=str(exc))
            
            
@blp.route("/enrollment/<uuid:enrollment_id>/shortage")
class AttendanceShortageResource(MethodView):

    @blp.doc(
        summary="Check attendance shortage",
        description=(
            "ADMIN only. Checks whether the student's attendance "
            "is below the specified minimum percentage. Default is 75%."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AttendanceShortageSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, enrollment_id):
        try:
            threshold = float(
                request.args.get("minimum_percentage", 75)
            )

            if not 0 < threshold <= 100:
                abort(
                    422,
                    message=(
                        "minimum_percentage must be greater than 0 "
                        "and at most 100."
                    ),
                )

            return get_attendance_shortage(
                enrollment_id,
                user_id=get_jwt_identity(),
                minimum_percentage=threshold,
            )

        except ValueError:
            abort(
                422,
                message="minimum_percentage must be a valid number.",
            )
        except EnrollmentNotFoundError as exc:
            abort(404, message=str(exc))
        except AttendancePermissionError as exc:
            abort(403, message=str(exc))