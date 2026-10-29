from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.auth.permissions import role_required
from app.courses.schemas import (
    CourseCreateSchema,
    CourseResponseSchema,
)
from app.courses.repository import (
    get_course_by_id,
    list_courses,
)
from app.courses.service import (
    create_course,
    CourseAlreadyExistsError,
    DepartmentNotFoundError,
    FacultyNotFoundError,
    InvalidCourseAssignmentError,
)


blp = Blueprint(
    "Courses",
    __name__,
    url_prefix="/courses",
    description="Course management.",
)


@blp.route("")
class CourseCollectionResource(MethodView):

    @blp.doc(
        summary="Create a course",
        description=(
            "ADMIN only. Creates a course assigned to an existing "
            "department and a faculty member from that department."
        ),
        security=[{"bearerAuth": []}],
    )
    @blp.arguments(CourseCreateSchema)
    @blp.response(201, CourseResponseSchema)
    @role_required("ADMIN")
    def post(self, data):
        try:
            return create_course(data)

        except CourseAlreadyExistsError as exc:
            abort(409, message=str(exc))

        except DepartmentNotFoundError as exc:
            abort(404, message=str(exc))

        except FacultyNotFoundError as exc:
            abort(404, message=str(exc))

        except InvalidCourseAssignmentError as exc:
            abort(409, message=str(exc))

    @blp.doc(
        summary="List all courses",
        description="ADMIN only. Returns courses ordered by course code.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, CourseResponseSchema(many=True))
    @role_required("ADMIN")
    def get(self):
        return list_courses()


@blp.route("/<uuid:course_id>")
class CourseDetailResource(MethodView):

    @blp.doc(
        summary="Get a course by UUID",
        description="ADMIN only. Returns one course by its UUID.",
        security=[{"bearerAuth": []}],
    )
    @blp.response(200, CourseResponseSchema)
    @role_required("ADMIN")
    def get(self, course_id):
        course = get_course_by_id(course_id)

        if course is None:
            abort(404, message="Course not found.")

        return course
