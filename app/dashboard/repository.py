from datetime import date
from sqlalchemy import and_, case, exists, func
from app.extensions import db
from app.models.student import Student
from app.models.faculty import Faculty
from app.models.department import Department
from app.models.course import Course
from app.models.course_offering import CourseOffering
from app.models.enrollment import Enrollment
from app.models.attendance import Attendance
from app.models.assessment import Assessment
from app.models.assessment_result import AssessmentResult


class DashboardRepository:

    @staticmethod
    def get_admin_overview():
        """Fetch global dashboard metrics for administrators."""

        total_students = db.session.query(
            func.count(Student.id)
        ).scalar() or 0

        total_faculty = db.session.query(
            func.count(Faculty.id)
        ).scalar() or 0

        total_departments = db.session.query(
            func.count(Department.id)
        ).scalar() or 0

        total_courses = db.session.query(
            func.count(Course.id)
        ).scalar() or 0

        active_enrollments = db.session.query(
            func.count(Enrollment.id)
        ).filter(
            Enrollment.status == "ENROLLED"
        ).scalar() or 0

        attendance_stats = db.session.query(
            func.count(Attendance.id).label("total_records"),
            func.sum(
                case(
                    (Attendance.status == "PRESENT", 1),
                    else_=0,
                )
            ).label("present_count"),
            func.sum(
                case(
                    (Attendance.status == "ABSENT", 1),
                    else_=0,
                )
            ).label("absent_count"),
            func.sum(
                case(
                    (Attendance.status == "LATE", 1),
                    else_=0,
                )
            ).label("late_count"),
        ).first()

        total_attendance_records = attendance_stats.total_records or 0
        present_count = attendance_stats.present_count or 0
        absent_count = attendance_stats.absent_count or 0
        late_count = attendance_stats.late_count or 0

        recorded_classes = present_count + absent_count + late_count

        overall_attendance_percentage = (
            round(
                ((present_count + late_count) / recorded_classes) * 100,
                2,
            )
            if recorded_classes
            else 0.0
        )

        total_assessment_results = db.session.query(
            func.count(AssessmentResult.id)
        ).scalar() or 0

        result_stats = db.session.query(
            func.coalesce(
                func.sum(AssessmentResult.marks_obtained), 0
            ).label("obtained_marks"),
            func.coalesce(
                func.sum(Assessment.max_marks), 0
            ).label("maximum_marks"),
        ).join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        ).first()

        obtained_marks = float(result_stats.obtained_marks or 0)
        maximum_marks = float(result_stats.maximum_marks or 0)

        overall_result_percentage = (
            round((obtained_marks / maximum_marks) * 100, 2)
            if maximum_marks > 0
            else 0.0
        )

        return {
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_departments": total_departments,
            "total_courses": total_courses,
            "active_enrollments": active_enrollments,
            "total_attendance_records": total_attendance_records,
            "overall_attendance_percentage": overall_attendance_percentage,
            "total_assessment_results": total_assessment_results,
            "overall_result_percentage": overall_result_percentage,
        }

    @staticmethod
    def get_faculty_overview(faculty_id):
        """Fetch dashboard metrics for a faculty member's offerings."""

        assigned_courses = db.session.query(
            func.count(func.distinct(CourseOffering.course_id))
        ).filter(
            CourseOffering.faculty_id == faculty_id
        ).scalar() or 0

        active_enrollments = db.session.query(
            func.count(Enrollment.id)
        ).join(
            CourseOffering,
            Enrollment.offering_id == CourseOffering.id,
        ).filter(
            CourseOffering.faculty_id == faculty_id,
            Enrollment.status == "ENROLLED",
        ).scalar() or 0

        attendance_stats = db.session.query(
            func.count(Attendance.id).label("total_records"),
            func.sum(
                case(
                    (Attendance.status == "PRESENT", 1),
                    else_=0,
                )
            ).label("present_count"),
            func.sum(
                case(
                    (Attendance.status == "ABSENT", 1),
                    else_=0,
                )
            ).label("absent_count"),
            func.sum(
                case(
                    (Attendance.status == "LATE", 1),
                    else_=0,
                )
            ).label("late_count"),
        ).join(
            Enrollment,
            Attendance.enrollment_id == Enrollment.id,
        ).join(
            CourseOffering,
            Enrollment.offering_id == CourseOffering.id,
        ).filter(
            CourseOffering.faculty_id == faculty_id,
        ).first()

        total_records = attendance_stats.total_records or 0
        present_count = attendance_stats.present_count or 0
        absent_count = attendance_stats.absent_count or 0
        late_count = attendance_stats.late_count or 0

        recorded_classes = present_count + absent_count + late_count

        attendance_percentage = (
            round(
                ((present_count + late_count) / recorded_classes) * 100,
                2,
            )
            if recorded_classes
            else 0.0
        )

        assessment_stats = db.session.query(
            func.count(AssessmentResult.id).label("total_results"),
            func.coalesce(
                func.sum(AssessmentResult.marks_obtained), 0
            ).label("obtained_marks"),
            func.coalesce(
                func.sum(Assessment.max_marks), 0
            ).label("maximum_marks"),
        ).join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        ).join(
            CourseOffering,
            Assessment.offering_id == CourseOffering.id,
        ).filter(
            CourseOffering.faculty_id == faculty_id,
        ).first()

        obtained_marks = float(assessment_stats.obtained_marks or 0)
        maximum_marks = float(assessment_stats.maximum_marks or 0)

        result_percentage = (
            round((obtained_marks / maximum_marks) * 100, 2)
            if maximum_marks > 0
            else 0.0
        )

        return {
            "assigned_courses": assigned_courses,
            "active_enrollments": active_enrollments,
            "total_attendance_records": total_records,
            "overall_attendance_percentage": attendance_percentage,
            "total_assessment_results": assessment_stats.total_results or 0,
            "overall_result_percentage": result_percentage,
        }

    @staticmethod
    def get_student_overview(student_id):
        """Fetch dashboard metrics for one student."""

        active_enrollments = db.session.query(
            func.count(Enrollment.id)
        ).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == "ENROLLED",
        ).scalar() or 0

        attendance_stats = db.session.query(
            func.count(Attendance.id).label("total_records"),
            func.sum(
                case(
                    (Attendance.status == "PRESENT", 1),
                    else_=0,
                )
            ).label("present_count"),
            func.sum(
                case(
                    (Attendance.status == "ABSENT", 1),
                    else_=0,
                )
            ).label("absent_count"),
            func.sum(
                case(
                    (Attendance.status == "LATE", 1),
                    else_=0,
                )
            ).label("late_count"),
        ).join(
            Enrollment,
            Attendance.enrollment_id == Enrollment.id,
        ).filter(
            Enrollment.student_id == student_id,
        ).first()

        total_records = attendance_stats.total_records or 0
        present_count = attendance_stats.present_count or 0
        absent_count = attendance_stats.absent_count or 0
        late_count = attendance_stats.late_count or 0

        recorded_classes = present_count + absent_count + late_count

        attendance_percentage = (
            round(
                ((present_count + late_count) / recorded_classes) * 100,
                2,
            )
            if recorded_classes
            else 0.0
        )

        result_stats = db.session.query(
            func.count(AssessmentResult.id).label("total_results"),
            func.coalesce(
                func.sum(AssessmentResult.marks_obtained), 0
            ).label("obtained_marks"),
            func.coalesce(
                func.sum(Assessment.max_marks), 0
            ).label("maximum_marks"),
        ).join(
            Enrollment,
            AssessmentResult.enrollment_id == Enrollment.id,
        ).join(
            Assessment,
            AssessmentResult.assessment_id == Assessment.id,
        ).filter(
            Enrollment.student_id == student_id,
        ).first()

        obtained_marks = float(result_stats.obtained_marks or 0)
        maximum_marks = float(result_stats.maximum_marks or 0)

        result_percentage = (
            round((obtained_marks / maximum_marks) * 100, 2)
            if maximum_marks > 0
            else 0.0
        )

        # Only assessments belonging to this student's enrolled offerings
        # are considered. Existing results are checked per student enrollment.
        upcoming_assessments = db.session.query(
            Assessment
        ).join(
            Enrollment,
            Assessment.offering_id == Enrollment.offering_id,
        ).filter(
            Enrollment.student_id == student_id,
            Enrollment.status == "ENROLLED",
            Enrollment.offering_id.isnot(None),
            Assessment.assessment_date >= date.today(),
            ~exists().where(
                and_(
                    AssessmentResult.assessment_id == Assessment.id,
                    AssessmentResult.enrollment_id == Enrollment.id,
                )
            ),
        ).order_by(
            Assessment.assessment_date.asc(),
            Assessment.id.asc(),
        ).all()

        return {
            "active_enrollments": active_enrollments,
            "total_attendance_records": total_records,
            "overall_attendance_percentage": attendance_percentage,
            "total_assessment_results": result_stats.total_results or 0,
            "overall_result_percentage": result_percentage,
            "upcoming_assessments": upcoming_assessments,
        }
