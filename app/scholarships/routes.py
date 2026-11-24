from flask import redirect
from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from flask_smorest import Blueprint, abort

from app.auth.permissions import role_required
from app.auth.repository import get_user_by_id
from app.scholarships import service
from app.scholarships.schemas import (
    ConcessionCreateSchema,
    FeeAdjustmentVoidSchema,
    MyScholarshipApplicationQuerySchema,
    MyScholarshipAwardQuerySchema,
    PageQuerySchema,
    ScholarshipApplicationCreateSchema,
    ScholarshipApplicationDocumentCollectionResponseSchema,
    ScholarshipApplicationDocumentResponseSchema,
    ScholarshipApplicationDocumentUploadSchema,
    ScholarshipApplicationPaginatedResponseSchema,
    ScholarshipApplicationQuerySchema,
    ScholarshipApplicationResponseSchema,
    ScholarshipApproveSchema,
    ScholarshipAwardApplyResponseSchema,
    ScholarshipAwardPaginatedResponseSchema,
    ScholarshipAwardQuerySchema,
    ScholarshipAwardResponseSchema,
    ScholarshipFeeAdjustmentPaginatedResponseSchema,
    ScholarshipFeeAdjustmentQuerySchema,
    ScholarshipFeeAdjustmentResponseSchema,
    ScholarshipProgramCreateSchema,
    ScholarshipProgramPaginatedResponseSchema,
    ScholarshipProgramQuerySchema,
    ScholarshipProgramResponseSchema,
    ScholarshipProgramUpdateSchema,
    ScholarshipRejectSchema,
)
from app.scholarships.service import ScholarshipModuleError


blp = Blueprint(
    "Scholarships",
    __name__,
    url_prefix="/scholarships",
    description="Scholarship applications, awards, and fee concessions.",
)


def _run(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except ScholarshipModuleError as exc:
        abort(exc.status_code, message=str(exc))


def _actor_role():
    user = get_user_by_id(get_jwt_identity())
    if user is None or user.role is None:
        abort(401, message="Authenticated user or role was not found.")
    return user.role.role_name.strip().upper()


@blp.route("/programs")
class ScholarshipProgramCollectionResource(MethodView):
    @blp.doc(
        summary="Create a scholarship program",
        description="Creates a draft scholarship program. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipProgramCreateSchema)
    @blp.response(201, ScholarshipProgramResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        return _run(service.create_program, data)

    @blp.doc(
        summary="List scholarship programs",
        description="Returns paginated scholarship programs. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipProgramQuerySchema, location="query")
    @blp.response(200, ScholarshipProgramPaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.list_admin_programs,
            page=query["page"],
            per_page=query["per_page"],
            academic_year_id=query.get("academic_year_id"),
            semester_id=query.get("semester_id"),
            department_id=query.get("department_id"),
            status=query.get("status"),
        )


@blp.route("/programs/open")
class OpenScholarshipProgramCollectionResource(MethodView):
    @blp.doc(
        summary="List scholarships available to the authenticated student",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(PageQuerySchema, location="query")
    @blp.response(200, ScholarshipProgramPaginatedResponseSchema)
    @role_required("STUDENT")
    def get(self, query):
        return _run(
            service.list_open_programs,
            get_jwt_identity(),
            page=query["page"],
            per_page=query["per_page"],
        )


@blp.route("/programs/<uuid:program_id>")
class ScholarshipProgramDetailResource(MethodView):
    @blp.doc(
        summary="Get scholarship program details",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipProgramResponseSchema)
    @role_required("ADMIN")
    def get(self, program_id):
        return _run(service.get_program, program_id)

    @blp.doc(
        summary="Update a draft scholarship program",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipProgramUpdateSchema)
    @blp.response(200, ScholarshipProgramResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, program_id):
        return _run(service.update_program, program_id, data)


@blp.route("/programs/<uuid:program_id>/open")
class ScholarshipProgramOpenResource(MethodView):
    @blp.doc(
        summary="Open a scholarship program for applications",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipProgramResponseSchema)
    @role_required("ADMIN")
    def post(self, program_id):
        return _run(service.open_program, program_id)


@blp.route("/programs/<uuid:program_id>/close")
class ScholarshipProgramCloseResource(MethodView):
    @blp.doc(
        summary="Close a scholarship program",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipProgramResponseSchema)
    @role_required("ADMIN")
    def post(self, program_id):
        return _run(service.close_program, program_id)


@blp.route("/programs/<uuid:program_id>/archive")
class ScholarshipProgramArchiveResource(MethodView):
    @blp.doc(
        summary="Archive a scholarship program",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipProgramResponseSchema)
    @role_required("ADMIN")
    def post(self, program_id):
        return _run(service.archive_program, program_id)


@blp.route("/programs/<uuid:program_id>/applications")
class ScholarshipApplicationSubmissionResource(MethodView):
    @blp.doc(
        summary="Apply to a scholarship program",
        description="Students may apply once while the program is accepting applications.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipApplicationCreateSchema)
    @blp.response(201, ScholarshipApplicationResponseSchema)
    @role_required("STUDENT")
    def post(self, data, program_id):
        return _run(
            service.submit_application,
            program_id,
            get_jwt_identity(),
            data["statement"],
        )


@blp.route("/applications")
class ScholarshipApplicationCollectionResource(MethodView):
    @blp.doc(
        summary="List scholarship applications",
        description="Returns paginated applications for review. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipApplicationQuerySchema, location="query")
    @blp.response(200, ScholarshipApplicationPaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.list_admin_applications,
            page=query["page"],
            per_page=query["per_page"],
            program_id=query.get("program_id"),
            student_id=query.get("student_id"),
            status=query.get("status"),
        )


@blp.route("/applications/me")
class MyScholarshipApplicationCollectionResource(MethodView):
    @blp.doc(
        summary="List the authenticated student's scholarship applications",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(MyScholarshipApplicationQuerySchema, location="query")
    @blp.response(200, ScholarshipApplicationPaginatedResponseSchema)
    @role_required("STUDENT")
    def get(self, query):
        return _run(
            service.list_my_applications,
            get_jwt_identity(),
            page=query["page"],
            per_page=query["per_page"],
            status=query.get("status"),
        )


@blp.route("/applications/<uuid:application_id>")
class ScholarshipApplicationDetailResource(MethodView):
    @blp.doc(
        summary="Get a scholarship application",
        description="Students may view only their own application. ADMIN may review any application.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipApplicationResponseSchema)
    @role_required("ADMIN", "STUDENT")
    def get(self, application_id):
        return _run(
            service.get_application_for_user,
            application_id,
            get_jwt_identity(),
            _actor_role(),
        )


@blp.route("/applications/<uuid:application_id>/documents")
class ScholarshipApplicationDocumentCollectionResource(MethodView):
    @blp.doc(
        summary="Upload a supporting PDF for a pending scholarship application",
        description="Send multipart/form-data with the required `file` field. Up to five PDFs of 2 MiB each are accepted.",
        security=[{"bearerAuth": []}],
        responses={
            403: {"description": "Only the application owner may upload documents."},
            404: {"description": "The scholarship application was not found."},
            409: {"description": "The application is not pending or its document limit is reached."},
            422: {"description": "The PDF is invalid or too large."},
            503: {"description": "PDF storage is unavailable."},
        },
    )
    @blp.arguments(
        ScholarshipApplicationDocumentUploadSchema,
        location="files",
    )
    @blp.response(201, ScholarshipApplicationDocumentResponseSchema)
    @role_required("STUDENT")
    def post(self, data, application_id):
        return _run(
            service.add_application_document,
            application_id,
            get_jwt_identity(),
            data["file"],
        )

    @blp.doc(
        summary="List supporting documents for an application",
        description="Students may view their own document metadata; ADMIN may view any application.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipApplicationDocumentCollectionResponseSchema)
    @role_required("ADMIN", "STUDENT")
    def get(self, application_id):
        return _run(
            service.list_application_documents,
            application_id,
            get_jwt_identity(),
            _actor_role(),
        )


@blp.route(
    "/applications/<uuid:application_id>/documents/<uuid:document_id>"
)
class ScholarshipApplicationDocumentDetailResource(MethodView):
    @blp.doc(
        summary="Download a scholarship application supporting PDF",
        description="Redirects to a short-lived private R2 download URL.",
        security=[{"bearerAuth": []}],
        responses={302: {"description": "Redirects to the signed private PDF URL."}},
    )
    @role_required("ADMIN", "STUDENT")
    def get(self, application_id, document_id):
        url = _run(
            service.get_application_document_url,
            application_id,
            document_id,
            get_jwt_identity(),
            _actor_role(),
        )
        response = redirect(url, code=302)
        response.headers["Cache-Control"] = "no-store"
        return response


@blp.route("/applications/<uuid:application_id>/withdraw")
class ScholarshipApplicationWithdrawResource(MethodView):
    @blp.doc(
        summary="Withdraw a submitted scholarship application",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipApplicationResponseSchema)
    @role_required("STUDENT")
    def post(self, application_id):
        return _run(
            service.withdraw_application,
            application_id,
            get_jwt_identity(),
        )


@blp.route("/applications/<uuid:application_id>/approve")
class ScholarshipApplicationApproveResource(MethodView):
    @blp.doc(
        summary="Approve an application and create its scholarship award",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipApproveSchema)
    @blp.response(200, ScholarshipApplicationResponseSchema)
    @role_required("ADMIN")
    def post(self, data, application_id):
        return _run(
            service.decide_application,
            application_id,
            get_jwt_identity(),
            True,
            award_value=data["award_value"],
            award_reason=data.get("award_reason"),
            decision_notes=data.get("decision_notes"),
        )


@blp.route("/applications/<uuid:application_id>/reject")
class ScholarshipApplicationRejectResource(MethodView):
    @blp.doc(
        summary="Reject a scholarship application",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipRejectSchema)
    @blp.response(200, ScholarshipApplicationResponseSchema)
    @role_required("ADMIN")
    def post(self, data, application_id):
        return _run(
            service.decide_application,
            application_id,
            get_jwt_identity(),
            False,
            decision_notes=data["decision_notes"],
        )


@blp.route("/awards")
class ScholarshipAwardCollectionResource(MethodView):
    @blp.doc(
        summary="List scholarship awards",
        description="Returns paginated scholarship awards. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ScholarshipAwardQuerySchema, location="query")
    @blp.response(200, ScholarshipAwardPaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.list_admin_awards,
            page=query["page"],
            per_page=query["per_page"],
            student_id=query.get("student_id"),
            program_id=query.get("program_id"),
            status=query.get("status"),
        )


@blp.route("/awards/me")
class MyScholarshipAwardCollectionResource(MethodView):
    @blp.doc(
        summary="List the authenticated student's scholarship awards",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(MyScholarshipAwardQuerySchema, location="query")
    @blp.response(200, ScholarshipAwardPaginatedResponseSchema)
    @role_required("STUDENT")
    def get(self, query):
        return _run(
            service.list_my_awards,
            get_jwt_identity(),
            page=query["page"],
            per_page=query["per_page"],
            status=query.get("status"),
        )


@blp.route("/awards/<uuid:award_id>/apply")
class ScholarshipAwardApplyResource(MethodView):
    @blp.doc(
        summary="Apply an approved scholarship award to open fee charges",
        description=(
            "Creates separate, auditable fee adjustments. Original charges "
            "remain unchanged. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, ScholarshipAwardApplyResponseSchema)
    @role_required("ADMIN")
    def post(self, award_id):
        return _run(service.apply_award, award_id)


@blp.route("/awards/<uuid:award_id>/revoke")
class ScholarshipAwardRevokeResource(MethodView):
    @blp.doc(
        summary="Revoke an award and void its active fee adjustments",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeAdjustmentVoidSchema)
    @blp.response(200, ScholarshipAwardResponseSchema)
    @role_required("ADMIN")
    def post(self, data, award_id):
        return _run(
            service.revoke_award,
            award_id,
            get_jwt_identity(),
            data["reason"],
        )


@blp.route("/concessions")
class FeeConcessionCollectionResource(MethodView):
    @blp.doc(
        summary="Grant a direct fee concession",
        description="Records an audited fee credit without changing the original charge. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(ConcessionCreateSchema)
    @blp.response(201, ScholarshipFeeAdjustmentResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        return _run(
            service.create_concession,
            data,
            get_jwt_identity(),
        )


@blp.route("/adjustments")
class FeeAdjustmentCollectionResource(MethodView):
    @blp.doc(
        summary="List scholarship and concession adjustments",
        description="Returns paginated fee adjustments. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        ScholarshipFeeAdjustmentQuerySchema,
        location="query",
    )
    @blp.response(200, ScholarshipFeeAdjustmentPaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.list_admin_adjustments,
            page=query["page"],
            per_page=query["per_page"],
            student_id=query.get("student_id"),
            charge_id=query.get("charge_id"),
            kind=query.get("kind"),
            status=query.get("status"),
        )


@blp.route("/adjustments/<uuid:adjustment_id>/void")
class FeeAdjustmentVoidResource(MethodView):
    @blp.doc(
        summary="Void a scholarship or concession adjustment",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeAdjustmentVoidSchema)
    @blp.response(200, ScholarshipFeeAdjustmentResponseSchema)
    @role_required("ADMIN")
    def post(self, data, adjustment_id):
        return _run(
            service.void_adjustment,
            adjustment_id,
            get_jwt_identity(),
            data["reason"],
        )
