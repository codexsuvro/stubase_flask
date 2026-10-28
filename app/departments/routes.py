from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.departments.schemas import (
    DepartmentCreateSchema,
    DepartmentResponseSchema,
    DepartmentHODAssignSchema,
)
from app.departments.repository import (
    get_department_by_id,
    list_departments,
)
from app.departments.service import (
    create_department,
    DepartmentAlreadyExistsError,
    assign_department_hod,
    DepartmentNotFoundError,
    FacultyNotFoundError,
    InvalidDepartmentHODError,
)


blp = Blueprint(
    "Departments",
    __name__,
    url_prefix="/departments",
    description="Department management.",
)


@blp.route("")
class DepartmentCollectionResource(MethodView):

    @blp.doc(
        summary="Create a department",
        description="ADMIN only. Creates a new department.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(DepartmentCreateSchema)
    @blp.response(201, DepartmentResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_department(data)
        except DepartmentAlreadyExistsError as exc:
            abort(409, message=str(exc))
        except ValueError as exc:
            abort(400, message=str(exc))

    @blp.doc(
        summary="List all departments",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, DepartmentResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        return list_departments()


@blp.route("/<uuid:department_id>")
class DepartmentDetailResource(MethodView):

    @blp.doc(
        summary="Get a department by UUID",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, DepartmentResponseSchema)
    @role_required("ADMIN")
    def get(self, department_id):
        department = get_department_by_id(department_id)

        if department is None:
            abort(404, message="Department not found.")

        return department
    

@blp.route("/<uuid:department_id>/hod")
class DepartmentHODResource(MethodView):

    @blp.doc(
        summary="Assign a Faculty as department HOD",
        description="ADMIN only. Assigns an existing Faculty from the same department as its HOD.",
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(DepartmentHODAssignSchema)
    @blp.response(200, DepartmentResponseSchema)
    @role_required("ADMIN")
    def put(self, data, department_id):
        try:
            return assign_department_hod(
                department_id=department_id,
                faculty_user_id=data["faculty_user_id"],
            )
        except DepartmentNotFoundError as exc:
            abort(404, message=str(exc))
        except FacultyNotFoundError as exc:
            abort(404, message=str(exc))
        except InvalidDepartmentHODError as exc:
            abort(409, message=str(exc))
