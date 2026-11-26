from flask import redirect
from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from flask_smorest import Blueprint, abort

from app.auth.permissions import role_required
from app.auth.repository import get_user_by_id
from app.finance import service
from app.finance.schemas import (
    FeeStructureCreateSchema,
    FeeStructurePaginatedResponseSchema,
    FeeStructureQuerySchema,
    FeeStructureResponseSchema,
    FeeStructureUpdateSchema,
    FeeChargeApplyResponseSchema,
    FeeChargeApplySchema,
    FeeChargePaginatedResponseSchema,
    FeeChargeQuerySchema,
    FeeChargeResponseSchema,
    FeeChargeVoidSchema,
    MyFeeChargeQuerySchema,
    FeeInvoiceCreateSchema,
    FeeInvoicePaginatedResponseSchema,
    FeeInvoiceQuerySchema,
    FeeInvoiceResponseSchema,
    FeeInvoiceVoidSchema,
    MyFeeInvoiceQuerySchema,
    FeePaymentCreateSchema,
    FeeInvoicePaymentQuerySchema,
    FeePaymentPaginatedResponseSchema,
    FeePaymentQuerySchema,
    FeePaymentResponseSchema,
    MyFeePaymentQuerySchema,
)
from app.finance.service import FinanceModuleError


blp = Blueprint(
    "Finance",
    __name__,
    url_prefix="/finance",
    description="Fee structure management.",
)


def _run(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except FinanceModuleError as exc:
        abort(exc.status_code, message=str(exc))


def _invoice_actor_role():
    user = get_user_by_id(get_jwt_identity())
    if user is None or user.role is None:
        abort(401, message="Authenticated user or role was not found.")
    return user.role.role_name.strip().upper()


@blp.route("/fee-structures")
class FeeStructureCollectionResource(MethodView):
    @blp.doc(
        summary="Create a draft fee structure",
        description=(
            "Creates a versioned fee schedule for a department and semester, "
            "optionally limited to a course offering. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeStructureCreateSchema)
    @blp.response(201, FeeStructureResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        return _run(service.create_fee_structure, data)

    @blp.doc(
        summary="List fee structures",
        description="Returns paginated fee structures with optional scope filters. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeStructureQuerySchema, location="query")
    @blp.response(200, FeeStructurePaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.get_fee_structures,
            page=query["page"],
            per_page=query["per_page"],
            academic_year_id=query.get("academic_year_id"),
            semester_id=query.get("semester_id"),
            department_id=query.get("department_id"),
            course_offering_id=query.get("course_offering_id"),
            status=query.get("status"),
        )


@blp.route("/fee-structures/<uuid:fee_structure_id>")
class FeeStructureDetailResource(MethodView):
    @blp.doc(
        summary="Get fee structure details",
        description="Returns a fee structure and its line items. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, FeeStructureResponseSchema)
    @role_required("ADMIN")
    def get(self, fee_structure_id):
        return _run(service.get_fee_structure, fee_structure_id)

    @blp.doc(
        summary="Update a draft fee structure",
        description=(
            "Only DRAFT fee structures may be edited. Updating items replaces "
            "the complete item list. Create a new version after activation. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeStructureUpdateSchema)
    @blp.response(200, FeeStructureResponseSchema)
    @role_required("ADMIN")
    def patch(self, data, fee_structure_id):
        return _run(
            service.update_fee_structure,
            fee_structure_id,
            data,
        )


@blp.route("/fee-structures/<uuid:fee_structure_id>/activate")
class FeeStructureActivateResource(MethodView):
    @blp.doc(
        summary="Activate a fee structure",
        description=(
            "Activates a complete draft. Only one version per scope and fee "
            "code may be active at a time. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, FeeStructureResponseSchema)
    @role_required("ADMIN")
    def post(self, fee_structure_id):
        return _run(service.activate_fee_structure, fee_structure_id)


@blp.route("/fee-structures/<uuid:fee_structure_id>/archive")
class FeeStructureArchiveResource(MethodView):
    @blp.doc(
        summary="Archive a fee structure",
        description="Archives a draft or active fee structure without deleting its history. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, FeeStructureResponseSchema)
    @role_required("ADMIN")
    def post(self, fee_structure_id):
        return _run(service.archive_fee_structure, fee_structure_id)


@blp.route("/fee-structures/<uuid:fee_structure_id>/apply")
class FeeStructureApplyResource(MethodView):
    @blp.doc(
        summary="Apply an active fee structure to eligible students",
        description=(
            "Creates immutable charge snapshots for currently enrolled "
            "students in the structure's department and semester. Offering-"
            "scoped structures apply only to students enrolled in that offering. "
            "Repeated application is idempotent. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeChargeApplySchema)
    @blp.response(200, FeeChargeApplyResponseSchema)
    @role_required("ADMIN")
    def post(self, data, fee_structure_id):
        return _run(
            service.apply_fee_structure,
            fee_structure_id,
            due_date=data.get("due_date"),
        )


@blp.route("/charges")
class FeeChargeCollectionResource(MethodView):
    @blp.doc(
        summary="List student fee charges",
        description="Returns paginated fee charges. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeChargeQuerySchema, location="query")
    @blp.response(200, FeeChargePaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.get_fee_charges,
            page=query["page"],
            per_page=query["per_page"],
            student_id=query.get("student_id"),
            academic_year_id=query.get("academic_year_id"),
            semester_id=query.get("semester_id"),
            status=query.get("status"),
        )


@blp.route("/charges/me")
class MyFeeChargeCollectionResource(MethodView):
    @blp.doc(
        summary="List the authenticated student's fee charges",
        description="Students may view only their own charge records.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(MyFeeChargeQuerySchema, location="query")
    @blp.response(200, FeeChargePaginatedResponseSchema)
    @role_required("STUDENT")
    def get(self, query):
        return _run(
            service.get_my_fee_charges,
            get_jwt_identity(),
            page=query["page"],
            per_page=query["per_page"],
            academic_year_id=query.get("academic_year_id"),
            semester_id=query.get("semester_id"),
            status=query.get("status"),
        )


@blp.route("/charges/<uuid:charge_id>/void")
class FeeChargeVoidResource(MethodView):
    @blp.doc(
        summary="Void an open fee charge",
        description="Voids a charge without deleting its financial audit record. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeChargeVoidSchema)
    @blp.response(200, FeeChargeResponseSchema)
    @role_required("ADMIN")
    def post(self, data, charge_id):
        return _run(
            service.void_fee_charge,
            charge_id,
            get_jwt_identity(),
            data["reason"],
        )


@blp.route("/invoices")
class FeeInvoiceCollectionResource(MethodView):
    @blp.doc(
        summary="Issue an invoice for selected student charges",
        description=(
            "Creates an immutable invoice snapshot from 1-100 OPEN fee "
            "charges belonging to one student, semester, and currency. "
            "The PDF is stored privately. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeInvoiceCreateSchema)
    @blp.response(201, FeeInvoiceResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        return _run(
            service.create_invoice,
            data,
            get_jwt_identity(),
        )

    @blp.doc(
        summary="List fee invoices",
        description="Returns paginated invoices. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeInvoiceQuerySchema, location="query")
    @blp.response(200, FeeInvoicePaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.get_invoices,
            page=query["page"],
            per_page=query["per_page"],
            student_id=query.get("student_id"),
            academic_year_id=query.get("academic_year_id"),
            semester_id=query.get("semester_id"),
            status=query.get("status"),
        )


@blp.route("/invoices/me")
class MyFeeInvoiceCollectionResource(MethodView):
    @blp.doc(
        summary="List the authenticated student's invoices",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(MyFeeInvoiceQuerySchema, location="query")
    @blp.response(200, FeeInvoicePaginatedResponseSchema)
    @role_required("STUDENT")
    def get(self, query):
        return _run(
            service.get_my_invoices,
            get_jwt_identity(),
            page=query["page"],
            per_page=query["per_page"],
            academic_year_id=query.get("academic_year_id"),
            semester_id=query.get("semester_id"),
            status=query.get("status"),
        )


@blp.route("/invoices/<uuid:invoice_id>")
class FeeInvoiceDetailResource(MethodView):
    @blp.doc(
        summary="Get an invoice",
        description="Students may access only their own invoice.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, FeeInvoiceResponseSchema)
    @role_required("ADMIN", "STUDENT")
    def get(self, invoice_id):
        return _run(
            service.get_invoice_for_user,
            invoice_id,
            get_jwt_identity(),
            _invoice_actor_role(),
        )


@blp.route("/invoices/<uuid:invoice_id>/pdf")
class FeeInvoicePDFResource(MethodView):
    @blp.doc(
        summary="Download an invoice PDF",
        description=(
            "Redirects to a short-lived private PDF URL after checking "
            "invoice ownership."
        ),
        security=[{"bearerAuth": []}],
        responses={302: {"description": "Redirect to the private PDF."}},
    )
    @role_required("ADMIN", "STUDENT")
    def get(self, invoice_id):
        url = _run(
            service.get_invoice_pdf_url,
            invoice_id,
            get_jwt_identity(),
            _invoice_actor_role(),
        )
        response = redirect(url, code=302)
        response.headers["Cache-Control"] = "no-store"
        return response


@blp.route("/invoices/<uuid:invoice_id>/void")
class FeeInvoiceVoidResource(MethodView):
    @blp.doc(
        summary="Void an invoice",
        description=(
            "Voids an invoice while retaining its audit record and PDF. "
            "Its charges may then be re-invoiced. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeInvoiceVoidSchema)
    @blp.response(200, FeeInvoiceResponseSchema)
    @role_required("ADMIN")
    def post(self, data, invoice_id):
        return _run(
            service.void_invoice,
            invoice_id,
            get_jwt_identity(),
            data["reason"],
        )


@blp.route("/invoices/<uuid:invoice_id>/payments")
class FeeInvoicePaymentCollectionResource(MethodView):
    @blp.doc(
        summary="Record a payment against an invoice",
        description=(
            "Records an offline/manual payment and creates its private "
            "receipt PDF. Partial payments are supported. ADMIN only."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeePaymentCreateSchema)
    @blp.response(201, FeePaymentResponseSchema)
    @role_required("ADMIN")
    def post(self, data, invoice_id):
        return _run(
            service.create_payment,
            invoice_id,
            data,
            get_jwt_identity(),
        )

    @blp.doc(
        summary="List payments for an invoice",
        description=(
            "Admins may list any invoice's payments. Students may list only "
            "payments for their own invoices."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeeInvoicePaymentQuerySchema, location="query")
    @blp.response(200, FeePaymentPaginatedResponseSchema)
    @role_required("ADMIN", "STUDENT")
    def get(self, query, invoice_id):
        return _run(
            service.get_invoice_payments_for_user,
            invoice_id,
            get_jwt_identity(),
            _invoice_actor_role(),
            page=query["page"],
            per_page=query["per_page"],
        )


@blp.route("/payments")
class FeePaymentCollectionResource(MethodView):
    @blp.doc(
        summary="List recorded payments",
        description="Returns paginated payments with optional filters. ADMIN only.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(FeePaymentQuerySchema, location="query")
    @blp.response(200, FeePaymentPaginatedResponseSchema)
    @role_required("ADMIN")
    def get(self, query):
        return _run(
            service.get_payments,
            page=query["page"],
            per_page=query["per_page"],
            student_id=query.get("student_id"),
            invoice_id=query.get("invoice_id"),
            payment_method=query.get("payment_method"),
        )


@blp.route("/payments/me")
class MyFeePaymentCollectionResource(MethodView):
    @blp.doc(
        summary="List the authenticated student's payments",
        description="Students may view only their own recorded payments.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(MyFeePaymentQuerySchema, location="query")
    @blp.response(200, FeePaymentPaginatedResponseSchema)
    @role_required("STUDENT")
    def get(self, query):
        return _run(
            service.get_my_payments,
            get_jwt_identity(),
            page=query["page"],
            per_page=query["per_page"],
            invoice_id=query.get("invoice_id"),
        )


@blp.route("/payments/<uuid:payment_id>/receipt")
class FeePaymentReceiptResource(MethodView):
    @blp.doc(
        summary="Download a payment receipt PDF",
        description=(
            "Redirects to a short-lived private receipt URL after checking "
            "student ownership."
        ),
        security=[{"bearerAuth": []}],
        responses={302: {"description": "Redirect to the private receipt PDF."}},
    )
    @role_required("ADMIN", "STUDENT")
    def get(self, payment_id):
        url = _run(
            service.get_payment_receipt_url,
            payment_id,
            get_jwt_identity(),
            _invoice_actor_role(),
        )
        response = redirect(url, code=302)
        response.headers["Cache-Control"] = "no-store"
        return response
