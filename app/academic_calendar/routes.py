from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.academic_calendar.schemas import (
    AcademicYearCreateSchema,
    AcademicYearUpdateSchema,
    AcademicYearStatusSchema,
    AcademicYearResponseSchema,
    SemesterCreateSchema,
    SemesterUpdateSchema,
    SemesterStatusSchema,
    SemesterResponseSchema,
    SemesterFilterSchema,
)
from app.academic_calendar.service import (
    create_academic_year,
    get_academic_year,
    get_all_academic_years,
    update_academic_year,
    update_academic_year_status,
    create_semester,
    get_semester,
    get_all_semesters,
    update_semester,
    update_semester_status,
    AcademicYearNotFoundError,
    AcademicYearAlreadyExistsError,
    SemesterNotFoundError,
    SemesterAlreadyExistsError,
    InvalidAcademicCalendarError,
    ActiveAcademicYearExistsError,
    ActiveSemesterExistsError,
)


blp = Blueprint(
    "Academic Calendar",
    __name__,
    description="Academic year and semester management.",
)


def handle_calendar_error(exc):
    if isinstance(
        exc,
        (AcademicYearNotFoundError, SemesterNotFoundError),
    ):
        abort(404, message=str(exc))

    if isinstance(
        exc,
        (
            AcademicYearAlreadyExistsError,
            SemesterAlreadyExistsError,
            ActiveAcademicYearExistsError,
            ActiveSemesterExistsError,
            InvalidAcademicCalendarError,
        ),
    ):
        abort(409, message=str(exc))

    if isinstance(exc, ValueError):
        abort(400, message=str(exc))

    raise exc


# ==========================================================
# ACADEMIC YEARS
# ==========================================================

@blp.route("/academic-years")
class AcademicYearCollectionResource(MethodView):

    @blp.doc(
        summary="Create an academic year",
        description="ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AcademicYearCreateSchema)
    @blp.response(201, AcademicYearResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_academic_year(data)
        except Exception as exc:
            handle_calendar_error(exc)

    @blp.doc(
        summary="List academic years",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AcademicYearResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        return get_all_academic_years()


@blp.route("/academic-years/<uuid:academic_year_id>")
class AcademicYearDetailResource(MethodView):

    @blp.doc(
        summary="Get an academic year",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AcademicYearResponseSchema)
    @role_required("ADMIN")
    def get(self, academic_year_id):
        try:
            return get_academic_year(academic_year_id)
        except Exception as exc:
            handle_calendar_error(exc)

    @blp.doc(
        summary="Update an academic year",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AcademicYearUpdateSchema)
    @blp.response(200, AcademicYearResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, academic_year_id):
        try:
            return update_academic_year(
                academic_year_id,
                data,
            )
        except Exception as exc:
            handle_calendar_error(exc)


@blp.route("/academic-years/<uuid:academic_year_id>/status")
class AcademicYearStatusResource(MethodView):

    @blp.doc(
        summary="Update academic year status",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AcademicYearStatusSchema)
    @blp.response(200, AcademicYearResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, academic_year_id):
        try:
            return update_academic_year_status(
                academic_year_id,
                data["status"],
            )
        except Exception as exc:
            handle_calendar_error(exc)


# ==========================================================
# SEMESTERS
# ==========================================================

@blp.route("/semesters")
class SemesterCollectionResource(MethodView):

    @blp.doc(
        summary="Create a semester",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SemesterCreateSchema)
    @blp.response(201, SemesterResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_semester(data)
        except Exception as exc:
            handle_calendar_error(exc)

    @blp.doc(
        summary="List semesters",
        description="Optional filters: academic_year_id and status.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SemesterFilterSchema, location="query")
    @blp.response(200, SemesterResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self, filters):
        try:
            return get_all_semesters(
                academic_year_id=filters.get("academic_year_id"),
                status=filters.get("status"),
            )
        except Exception as exc:
            handle_calendar_error(exc)


@blp.route("/semesters/<uuid:semester_id>")
class SemesterDetailResource(MethodView):

    @blp.doc(
        summary="Get a semester",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SemesterResponseSchema)
    @role_required("ADMIN")
    def get(self, semester_id):
        try:
            return get_semester(semester_id)
        except Exception as exc:
            handle_calendar_error(exc)

    @blp.doc(
        summary="Update a semester",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SemesterUpdateSchema)
    @blp.response(200, SemesterResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, semester_id):
        try:
            return update_semester(
                semester_id,
                data,
            )
        except Exception as exc:
            handle_calendar_error(exc)


@blp.route("/semesters/<uuid:semester_id>/status")
class SemesterStatusResource(MethodView):

    @blp.doc(
        summary="Update semester status",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SemesterStatusSchema)
    @blp.response(200, SemesterResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, semester_id):
        try:
            return update_semester_status(
                semester_id,
                data["status"],
            )
        except Exception as exc:
            handle_calendar_error(exc)