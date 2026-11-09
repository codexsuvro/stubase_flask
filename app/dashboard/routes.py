from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import get_jwt_identity
from app.auth.permissions import role_required
from app.dashboard.schemas import (
    DashboardMetricsSchema,
    StudentDashboardSchema,
)
from app.dashboard.service import DashboardService


blp = Blueprint(
    "Dashboard",
    __name__,
    url_prefix="/dashboard",
    description="Role-based dashboard analytics.",
)


@blp.route("/admin")
class AdminDashboardResource(MethodView):

    @blp.doc(
        summary="Get administrator dashboard",
        description="Returns global academic and institutional metrics.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, DashboardMetricsSchema)
    @role_required("ADMIN")
    def get(self):

        return DashboardService.get_admin_dashboard()


@blp.route("/faculty")
class FacultyDashboardResource(MethodView):

    @blp.doc(
        summary="Get faculty dashboard",
        description=(
            "Returns dashboard metrics for courses assigned "
            "to the authenticated faculty member."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, DashboardMetricsSchema)
    @role_required("FACULTY")
    def get(self):

        return DashboardService.get_faculty_dashboard(
            user_id=get_jwt_identity()
        )


@blp.route("/student")
class StudentDashboardResource(MethodView):

    @blp.doc(
        summary="Get student dashboard",
        description=(
            "Returns academic metrics and upcoming assessments "
            "for the authenticated student."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, StudentDashboardSchema)
    @role_required("STUDENT")
    def get(self):

        return DashboardService.get_student_dashboard(
            user_id=get_jwt_identity()
        )
