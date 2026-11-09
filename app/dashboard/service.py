from werkzeug.exceptions import NotFound, Forbidden
from app.extensions import db
from app.models.faculty import Faculty
from app.models.student import Student
from app.dashboard.repository import DashboardRepository


class DashboardService:

    @staticmethod
    def get_admin_dashboard():
        return DashboardRepository.get_admin_overview()

    @staticmethod
    def get_faculty_dashboard(user_id):
        faculty = db.session.query(Faculty).filter_by(
            user_id=user_id
        ).first()

        if not faculty:
            raise NotFound("Faculty profile not found.")

        dashboard = DashboardRepository.get_faculty_overview(
            faculty.id
        )

        return dashboard

    @staticmethod
    def get_student_dashboard(user_id):
        student = db.session.query(Student).filter_by(
            user_id=user_id
        ).first()

        if not student:
            raise NotFound("Student profile not found.")

        dashboard = DashboardRepository.get_student_overview(
            student.id
        )

        return dashboard
