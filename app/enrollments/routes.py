from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.enrollments.schemas import (
    EnrollmentCreateSchema,
    EnrollmentResponseSchema,
)
from app.enrollments.repository import (
    get_enrollment_by_id,
    list_enrollments,
    list_enrollments_by_student,
)
from app.enrollments.service import (
    create_enrollment,
    StudentNotFoundError,
    CourseNotFoundError,
    InvalidEnrollmentError,
    DuplicateEnrollmentError,
)
from app.models.student import Student
from app.extensions import db


blp = Blueprint(
    "Enrollments",
    __name__,
    url_prefix="/enrollments",
    description="Student course enrollment management.",
)


@blp.route("")
class EnrollmentCollectionResource(MethodView):

    @blp.doc(
        summary="Enroll a student in a course",
        description=(
            "ADMIN only. Creates an enrollment after validating "
            "the student, course, department, semester, and duplicates."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(EnrollmentCreateSchema)
    @blp.response(201, EnrollmentResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_enrollment(data)

        except StudentNotFoundError as exc:
            abort(404, message=str(exc))

        except CourseNotFoundError as exc:
            abort(404, message=str(exc))

        except DuplicateEnrollmentError as exc:
            abort(409, message=str(exc))

        except InvalidEnrollmentError as exc:
            abort(409, message=str(exc))

    @blp.doc(
        summary="List all enrollments",
        description="ADMIN only. Returns all student course enrollments.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, EnrollmentResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        return list_enrollments()


@blp.route("/<uuid:enrollment_id>")
class EnrollmentDetailResource(MethodView):

    @blp.doc(
        summary="Get enrollment by UUID",
        description="ADMIN only. Returns one enrollment record.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, EnrollmentResponseSchema)
    @role_required("ADMIN")
    def get(self, enrollment_id):
        enrollment = get_enrollment_by_id(enrollment_id)

        if enrollment is None:
            abort(404, message="Enrollment not found.")

        return enrollment


@blp.route("/student/<uuid:student_id>")
class StudentEnrollmentResource(MethodView):

    @blp.doc(
        summary="List enrollments for a student",
        description=(
            "ADMIN only. Returns all enrollments belonging "
            "to the specified Student profile UUID."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, EnrollmentResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self, student_id):
        student = db.session.get(Student, student_id)

        if student is None:
            abort(404, message="Student not found.")

        return list_enrollments_by_student(student_id)