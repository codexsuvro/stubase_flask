from flask import redirect
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import get_jwt_identity
from app.auth.permissions import role_required
from app.auth.repository import get_user_by_id
from app.assignments.schemas import (
    AssignmentCreateSchema,
    AssignmentUpdateSchema,
    AssignmentStatusSchema,
    AssignmentQuerySchema,
    MyAssignmentQuerySchema,
    SubmissionQuerySchema,
    SubmissionPDFUploadSchema,
    SubmissionGradeSchema,
    AssignmentResponseSchema,
    SubmissionResponseSchema,
    AssignmentPaginatedResponseSchema,
    SubmissionPaginatedResponseSchema,
)
from app.assignments.service import (
    create_assignment,
    update_assignment,
    change_assignment_status,
    delete_assignment,
    get_assignment_for_user,
    list_assignments_for_user,
    list_my_assignments,
    submit_pdf_assignment,
    resubmit_pdf_assignment,
    list_assignment_submissions,
    get_submission_for_user,
    get_pdf_download_url,
    grade_submission,
    AssignmentNotFoundError,
    SubmissionNotFoundError,
    AssignmentOfferingNotFoundError,
    AssignmentAccessDeniedError,
    AssignmentValidationError,
    AssignmentConflictError,
    AssignmentFileNotFoundError,
)
from app.assignments.storage import AssignmentStorageError


blp = Blueprint(
    "Assignments",
    __name__,
    url_prefix="/assignments",
    description="Course assignment and submission management.",
)


def _actor_role():
    user = get_user_by_id(get_jwt_identity())

    if user is None or user.role is None:
        abort(
            401,
            message="Authenticated user or role was not found.",
        )

    return user.role.role_name.strip().upper()


def _handle_error(exc):
    if isinstance(
        exc,
        (
            AssignmentNotFoundError,
            SubmissionNotFoundError,
            AssignmentOfferingNotFoundError,
        ),
    ):
        abort(404, message=str(exc))

    if isinstance(exc, AssignmentAccessDeniedError):
        abort(403, message=str(exc))

    if isinstance(exc, AssignmentConflictError):
        abort(409, message=str(exc))

    if isinstance(exc, AssignmentValidationError):
        abort(422, message=str(exc))

    if isinstance(exc, AssignmentFileNotFoundError):
        abort(404, message=str(exc))

    if isinstance(exc, AssignmentStorageError):
        abort(503, message=str(exc))

    raise exc


@blp.route("")
class AssignmentCollectionResource(MethodView):

    @blp.doc(
        summary="Create an assignment",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssignmentCreateSchema)
    @blp.response(201, AssignmentResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def post(self, data):
        try:
            return create_assignment(
                data,
                get_jwt_identity(),
                _actor_role(),
            )
        except Exception as exc:
            _handle_error(exc)

    @blp.doc(
        summary="List assignments",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        AssignmentQuerySchema,
        location="query",
    )
    @blp.response(200, AssignmentPaginatedResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, query_args):
        try:
            return list_assignments_for_user(
                get_jwt_identity(),
                _actor_role(),
                page=query_args["page"],
                per_page=query_args["per_page"],
                offering_id=query_args.get("offering_id"),
                status=query_args.get("status"),
            )
        except Exception as exc:
            _handle_error(exc)


@blp.route("/my")
class MyAssignmentsResource(MethodView):

    @blp.doc(
        summary="List assignments for the authenticated student",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        MyAssignmentQuerySchema,
        location="query",
    )
    @blp.response(200, AssignmentPaginatedResponseSchema)
    @role_required("STUDENT")
    def get(self, query_args):
        try:
            return list_my_assignments(
                get_jwt_identity(),
                page=query_args["page"],
                per_page=query_args["per_page"],
                offering_id=query_args.get("offering_id"),
            )
        except Exception as exc:
            _handle_error(exc)


@blp.route("/<uuid:assignment_id>")
class AssignmentDetailResource(MethodView):

    @blp.doc(
        summary="Get assignment details",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, AssignmentResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, assignment_id):
        try:
            return get_assignment_for_user(
                assignment_id,
                get_jwt_identity(),
                _actor_role(),
            )
        except Exception as exc:
            _handle_error(exc)

    @blp.doc(
        summary="Update assignment",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssignmentUpdateSchema)
    @blp.response(200, AssignmentResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, assignment_id):
        try:
            return update_assignment(
                assignment_id,
                data,
                get_jwt_identity(),
                _actor_role(),
            )
        except Exception as exc:
            _handle_error(exc)

    @blp.doc(
        summary="Delete assignment without submissions",
        security=[{"bearerAuth": []}],
    )
    @blp.response(204)
    @role_required("ADMIN", "FACULTY")
    def delete(self, assignment_id):
        try:
            delete_assignment(
                assignment_id,
                get_jwt_identity(),
                _actor_role(),
            )

            return "", 204

        except Exception as exc:
            _handle_error(exc)


@blp.route("/<uuid:assignment_id>/status")
class AssignmentStatusResource(MethodView):

    @blp.doc(
        summary="Publish, draft or close an assignment",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(AssignmentStatusSchema)
    @blp.response(200, AssignmentResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, assignment_id):
        try:
            return change_assignment_status(
                assignment_id,
                data["status"],
                get_jwt_identity(),
                _actor_role(),
            )
        except Exception as exc:
            _handle_error(exc)


@blp.route("/<uuid:assignment_id>/submissions")
class AssignmentSubmissionCollectionResource(MethodView):

    @blp.doc(
        summary="List submissions for an assignment",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(
        SubmissionQuerySchema,
        location="query",
    )
    @blp.response(200, SubmissionPaginatedResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def get(self, query_args, assignment_id):
        try:
            return list_assignment_submissions(
                assignment_id,
                get_jwt_identity(),
                _actor_role(),
                page=query_args["page"],
                per_page=query_args["per_page"],
                status=query_args.get("status"),
            )
        except Exception as exc:
            _handle_error(exc)


@blp.route("/<uuid:assignment_id>/submissions/pdf")
class AssignmentPDFSubmissionResource(MethodView):

    @blp.doc(
        summary="Submit a PDF for an assignment",
        description=(
            "Send multipart/form-data with the required `file` field. "
            "Only PDFs up to 2 MiB are accepted."
        ),
        security=[{"bearerAuth": []}],
        responses={
            401: {"description": "Authentication is required."},
            403: {"description": "Only enrolled students may submit."},
            404: {"description": "The assignment was not found."},
            409: {"description": "A submission already exists."},
            413: {"description": "The request exceeds the 3 MiB request limit."},
            422: {"description": "The PDF or submission window is invalid."},
            503: {"description": "PDF storage is unavailable."},
        },
    )
    @blp.arguments(
        SubmissionPDFUploadSchema,
        location="files",
    )
    @blp.response(201, SubmissionResponseSchema)
    @role_required("STUDENT")
    def post(self, data, assignment_id):
        try:
            return submit_pdf_assignment(
                assignment_id,
                data["file"],
                get_jwt_identity(),
            )
        except Exception as exc:
            _handle_error(exc)


@blp.route("/submissions/<uuid:submission_id>")
class AssignmentSubmissionDetailResource(MethodView):

    @blp.doc(
        summary="Get an assignment submission",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, SubmissionResponseSchema)
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, submission_id):
        try:
            return get_submission_for_user(
                submission_id,
                get_jwt_identity(),
                _actor_role(),
            )
        except Exception as exc:
            _handle_error(exc)

@blp.route("/submissions/<uuid:submission_id>/pdf")
class AssignmentSubmissionPDFResource(MethodView):

    @blp.doc(
        summary="Download a submitted PDF",
        security=[{"bearerAuth": []}],
        responses={
            302: {
                "description": (
                    "Redirects to a temporary R2 download URL."
                )
            }
        },
    )
    @role_required("ADMIN", "FACULTY", "STUDENT")
    def get(self, submission_id):
        try:
            url = get_pdf_download_url(
                submission_id,
                get_jwt_identity(),
                _actor_role(),
            )
            response = redirect(url, code=302)
            response.headers["Cache-Control"] = "no-store"
            return response
        except Exception as exc:
            _handle_error(exc)

    @blp.doc(
        summary="Resubmit a PDF for an assignment",
        description=(
            "Send multipart/form-data with the required `file` field. "
            "Resubmission must be enabled for the assignment."
        ),
        security=[{"bearerAuth": []}],
        responses={
            401: {"description": "Authentication is required."},
            403: {"description": "Only the submission owner may resubmit."},
            404: {"description": "The submission was not found."},
            413: {"description": "The request exceeds the 3 MiB request limit."},
            422: {"description": "The PDF or resubmission rules are invalid."},
            503: {"description": "PDF storage is unavailable."},
        },
    )
    @blp.arguments(
        SubmissionPDFUploadSchema,
        location="files",
    )
    @blp.response(200, SubmissionResponseSchema)
    @role_required("STUDENT")
    def patch(self, data, submission_id):
        try:
            return resubmit_pdf_assignment(
                submission_id,
                data["file"],
                get_jwt_identity(),
            )
        except Exception as exc:
            _handle_error(exc)


@blp.route("/submissions/<uuid:submission_id>/grade")
class AssignmentSubmissionGradeResource(MethodView):

    @blp.doc(
        summary="Grade an assignment submission",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(SubmissionGradeSchema)
    @blp.response(200, SubmissionResponseSchema)
    @role_required("ADMIN", "FACULTY")
    def patch(self, data, submission_id):
        try:
            return grade_submission(
                submission_id,
                data,
                get_jwt_identity(),
                _actor_role(),
            )
        except Exception as exc:
            _handle_error(exc)
