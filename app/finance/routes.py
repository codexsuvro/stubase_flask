from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity
from flask_smorest import Blueprint, abort

from app.auth.permissions import role_required
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
