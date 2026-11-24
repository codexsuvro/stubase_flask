from app.models.role import Role
from app.models.user import User
from app.models.department import Department
from app.models.student import Student
from app.models.faculty import Faculty
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.attendance import Attendance
from app.models.token_blocklist import TokenBlocklist
from app.models.assessment import Assessment
from app.models.assessment_result import AssessmentResult
from app.models.academic_year import AcademicYear
from app.models.semester import Semester
from app.models.course_offering import CourseOffering
from app.timetable.models import Classroom, TimetableSlot
from app.models.course_prerequisite import CoursePrerequisite
from app.models.course_waitlist import CourseWaitlist
from app.models.grading_scheme import GradingScheme
from app.models.grade_scale import GradeScale
from app.models.course_grade import CourseGrade
from app.faculty_workload.models import FacultyWorkloadPolicy
from app.assignments.models import Assignment, AssignmentSubmission
from app.curricula.models import (
    Curriculum,
    CurriculumCourse,
    LearningOutcome,
    Syllabus,
    SyllabusTopic,
    SyllabusUnit,
    TopicLearningOutcome,
)
from app.announcements.models import Announcement
from app.notifications.models import Notification, NotificationDelivery
from app.finance.models import (
    FeeStructure,
    FeeStructureItem,
    StudentFeeCharge,
    FeeAdjustment,
)
from app.scholarships.models import (
    ScholarshipProgram,
    ScholarshipApplication,
    ScholarshipApplicationDocument,
    ScholarshipAward,
)
