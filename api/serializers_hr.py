from rest_framework import serializers

from assets.models import Asset, AssetAssignment
from attendance.models import Attendance
from benefits.models import Benefit, EmployeeBenefit
from discipline.models import Discipline, DisciplineAppeal
from employees.models import Employee
from exits.models import ExitChecklist, ExitProcess
from expenses.models import Expense, ExpenseCategory
from kin.models import Kin
from leave_policies.models import LeavePolicy, LeavePolicyAllocation
from leaves.models import Leave, LeaveBalance
from payroll.models import Salary
from performance.models import (
    Feedback,
    FeedbackRequest,
    FeedbackRound,
    PerformanceAppraisal,
    PerformanceGoal,
)
from recruitment.models import Application, JobPosting
from shifts.models import Shift, ShiftAssignment
from surveys.models import Survey, SurveyQuestion, SurveyResponse
from training.models import (
    Certification,
    DevelopmentPlan,
    EmployeeCertification,
    EmployeeSkill,
    Skill,
    TrainingCourse,
    TrainingRecord,
)


def employee_label(obj):
    return getattr(obj, 'full_name', str(obj))


class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    duration = serializers.IntegerField(read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Leave
        fields = '__all__'
        read_only_fields = ['status', 'applied_on', 'reviewed_by', 'reviewed_on']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    available_days = serializers.FloatField(read_only=True)

    class Meta:
        model = LeaveBalance
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'


class JobPostingSerializer(serializers.ModelSerializer):
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = '__all__'

    def get_application_count(self, obj):
        return obj.applications.count()


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_name = serializers.SerializerMethodField()
    resume_url = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = '__all__'

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    def get_resume_url(self, obj):
        if obj.resume:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.resume.url)
            return obj.resume.url
        return None


class SalarySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    month_name = serializers.CharField(read_only=True)
    total_earnings = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    total_deductions = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = Salary
        fields = '__all__'
        read_only_fields = ['net_salary', 'created_at', 'updated_at']


class PerformanceGoalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PerformanceGoal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PerformanceAppraisalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PerformanceAppraisal
        fields = '__all__'
        read_only_fields = ['overall_rating', 'created_at', 'submitted_at', 'reviewed_at', 'approved_at']


class FeedbackRoundSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = FeedbackRound
        fields = '__all__'
        read_only_fields = ['created_at']


class FeedbackRequestSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    giver_username = serializers.CharField(source='feedback_giver.username', read_only=True)
    round_name = serializers.CharField(source='feedback_round.name', read_only=True)
    has_feedback = serializers.SerializerMethodField()

    class Meta:
        model = FeedbackRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'submitted_at']

    def get_has_feedback(self, obj):
        return hasattr(obj, 'feedback')


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SkillSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Skill
        fields = '__all__'


class EmployeeSkillSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = EmployeeSkill
        fields = '__all__'


class TrainingCourseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    participants_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingCourse
        fields = '__all__'


class TrainingRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TrainingRecord
        fields = '__all__'


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class EmployeeCertificationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    certification_name = serializers.CharField(source='certification.name', read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = EmployeeCertification
        fields = '__all__'


class DevelopmentPlanSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DevelopmentPlan
        fields = '__all__'


class ExitProcessSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = ExitProcess
        fields = '__all__'


class ExitChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExitChecklist
        fields = '__all__'


class AssetSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_current_status_display', read_only=True)

    class Meta:
        model = Asset
        fields = '__all__'


class AssetAssignmentSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = AssetAssignment
        fields = '__all__'


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    shift_name = serializers.CharField(source='shift.shift_name', read_only=True)

    class Meta:
        model = ShiftAssignment
        fields = '__all__'


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = '__all__'

    def get_receipt_url(self, obj):
        if obj.receipt_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt_file.url)
            return obj.receipt_file.url
        return None


class BenefitSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_benefit_type_display', read_only=True)

    class Meta:
        model = Benefit
        fields = '__all__'


class EmployeeBenefitSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    benefit_name = serializers.CharField(source='benefit.name', read_only=True)

    class Meta:
        model = EmployeeBenefit
        fields = '__all__'


class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)

    class Meta:
        model = LeavePolicy
        fields = '__all__'


class LeavePolicyAllocationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    policy_name = serializers.CharField(source='policy.name', read_only=True)

    class Meta:
        model = LeavePolicyAllocation
        fields = '__all__'


class DisciplineSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    type_display = serializers.CharField(source='get_discipline_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Discipline
        fields = '__all__'


class DisciplineAppealSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DisciplineAppeal
        fields = '__all__'


class KinSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = Kin
        fields = '__all__'


class SurveySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Survey
        fields = '__all__'


class SurveyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestion
        fields = '__all__'


class SurveyResponseSerializer(serializers.ModelSerializer):
    survey_title = serializers.CharField(source='survey.title', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = SurveyResponse
        fields = '__all__'
