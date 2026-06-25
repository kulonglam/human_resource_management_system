from datetime import timedelta

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from accounts.access_control import can_access_employee, get_user_accessible_employees
from accounts.models import AuditLog, CustomUser
from assets.models import Asset, AssetAssignment
from attendance.models import Attendance
from benefits.models import Benefit, EmployeeBenefit
from departments.models import Department
from discipline.models import Discipline, DisciplineAppeal
from employees.models import Employee
from exits.models import ExitChecklist, ExitProcess
from expenses.models import Expense, ExpenseCategory
from kin.models import Kin
from leave_policies.models import LeavePolicy, LeavePolicyAllocation
from leaves.models import Leave, LeaveBalance
from payroll.models import Salary
from payroll.utils import generate_salary_slip_pdf
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

from .audit import log_action
from .mixins import EmployeeQuerysetMixin
from .notifications import notify_leave_decision, notify_leave_submitted
from .permissions import IsAdmin, IsAdminOrManager, IsAdminOrManagerOrReadOnly, IsAdminOrReadOnly
from .serializers import (
    AuditLogSerializer,
    DepartmentSerializer,
    EmployeeSerializer,
    EmployeeTerminateSerializer,
)
from .serializers_hr import (
    ApplicationSerializer,
    AssetAssignmentSerializer,
    AssetSerializer,
    AttendanceSerializer,
    BenefitSerializer,
    CertificationSerializer,
    DevelopmentPlanSerializer,
    DisciplineAppealSerializer,
    DisciplineSerializer,
    EmployeeBenefitSerializer,
    EmployeeCertificationSerializer,
    EmployeeSkillSerializer,
    ExitChecklistSerializer,
    ExitProcessSerializer,
    ExpenseCategorySerializer,
    ExpenseSerializer,
    FeedbackRequestSerializer,
    FeedbackRoundSerializer,
    FeedbackSerializer,
    JobPostingSerializer,
    KinSerializer,
    LeaveBalanceSerializer,
    LeavePolicyAllocationSerializer,
    LeavePolicySerializer,
    LeaveSerializer,
    PerformanceAppraisalSerializer,
    PerformanceGoalSerializer,
    SalarySerializer,
    ShiftAssignmentSerializer,
    ShiftSerializer,
    SkillSerializer,
    SurveyQuestionSerializer,
    SurveyResponseSerializer,
    SurveySerializer,
    TrainingCourseSerializer,
    TrainingRecordSerializer,
)


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        qs = get_user_accessible_employees(self.request.user).filter(is_active=True)
        query = self.request.query_params.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(job_title__icontains=query)
                | Q(department__name__icontains=query)
            )
        return qs.select_related('department')

    def retrieve(self, request, *args, **kwargs):
        employee = self.get_object()
        if not can_access_employee(request.user, employee):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        employee = self.get_object()
        if not can_access_employee(request.user, employee):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Use terminate action instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        if not request.user.is_admin:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        employee = self.get_object()
        serializer = EmployeeTerminateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee.is_active = False
        employee.termination_date = timezone.now().date()
        employee.exit_reason = serializer.validated_data['exit_reason']
        employee.exit_notes = serializer.validated_data.get('exit_notes', '')
        employee.save()
        try:
            user = CustomUser.objects.get(email=employee.email)
            user.is_active = False
            user.save()
        except CustomUser.DoesNotExist:
            pass
        return Response(EmployeeSerializer(employee, context={'request': request}).data)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class LeaveViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = LeaveSerializer

    def get_queryset(self):
        qs = Leave.objects.select_related('employee').order_by('-applied_on')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        leave = serializer.save()
        current_year = timezone.now().year
        try:
            balance = LeaveBalance.objects.get(
                employee=leave.employee,
                leave_type=leave.leave_type,
                year=current_year,
            )
            if balance.available_days < leave.duration:
                leave.delete()
                raise serializers.ValidationError(
                    f'Insufficient leave balance. Available: {balance.available_days} days.'
                )
            balance.pending_days += leave.duration
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass
        log_action(
            self.request, 'create', 'Leave', leave.id, str(leave),
            f'Leave submitted for {leave.employee.full_name}',
        )
        notify_leave_submitted(leave)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'detail': 'Leave is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        current_year = timezone.now().year
        try:
            balance = LeaveBalance.objects.get(
                employee=leave.employee, leave_type=leave.leave_type, year=current_year
            )
            balance.pending_days -= leave.duration
            balance.used_days += leave.duration
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass
        leave.status = 'approved'
        leave.reviewed_by = request.user.get_full_name() or request.user.username
        leave.reviewed_on = timezone.now()
        leave.save()
        log_action(request, 'approve', 'Leave', leave.id, str(leave), 'Leave approved')
        notify_leave_decision(leave, 'approved')
        return Response(LeaveSerializer(leave).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'detail': 'Leave is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        current_year = timezone.now().year
        try:
            balance = LeaveBalance.objects.get(
                employee=leave.employee, leave_type=leave.leave_type, year=current_year
            )
            balance.pending_days -= leave.duration
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass
        leave.status = 'rejected'
        leave.reviewed_by = request.user.get_full_name() or request.user.username
        leave.reviewed_on = timezone.now()
        leave.save()
        log_action(request, 'reject', 'Leave', leave.id, str(leave), 'Leave rejected')
        notify_leave_decision(leave, 'rejected')
        return Response(LeaveSerializer(leave).data)


class LeaveBalanceViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = LeaveBalance.objects.select_related('employee').order_by('-year', 'leave_type')
        year = self.request.query_params.get('year')
        if year:
            qs = qs.filter(year=year)
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class AttendanceViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = Attendance.objects.select_related('employee').order_by('-date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs


class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.all().order_by('-posted_on')
    serializer_class = JobPostingSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Application.objects.select_related('job').order_by('-applied_on')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class SalaryViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = SalarySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = Salary.objects.select_related('employee').order_by('-year', '-month')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month:
            qs = qs.filter(month=month)
        if year:
            qs = qs.filter(year=year)
        return qs

    @action(detail=True, methods=['get'])
    def slip(self, request, pk=None):
        salary = self.get_object()
        return generate_salary_slip_pdf(salary)


class PerformanceGoalViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = PerformanceGoalSerializer

    def get_queryset(self):
        qs = PerformanceGoal.objects.select_related('employee').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        serializer.save(set_by=self.request.user)


class PerformanceAppraisalViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = PerformanceAppraisalSerializer

    def get_queryset(self):
        qs = PerformanceAppraisal.objects.select_related('employee').order_by('-appraisal_period_end')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def submit(self, request, pk=None):
        appraisal = self.get_object()
        appraisal.status = 'submitted'
        appraisal.submitted_at = timezone.now()
        appraisal.save()
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        appraisal = self.get_object()
        appraisal.status = 'approved'
        appraisal.approved_at = timezone.now()
        appraisal.save()
        return Response(PerformanceAppraisalSerializer(appraisal).data)


class FeedbackRoundViewSet(viewsets.ModelViewSet):
    queryset = FeedbackRound.objects.all().order_by('-created_at')
    serializer_class = FeedbackRoundSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        reqs = instance.feedback_requests.select_related('recipient', 'feedback_giver').all()
        data['stats'] = {
            'total': reqs.count(),
            'submitted': reqs.filter(status='submitted').count(),
            'pending': reqs.filter(status='pending').count(),
        }
        data['requests'] = FeedbackRequestSerializer(
            reqs, many=True, context=self.get_serializer_context()
        ).data
        return Response(data)

    @action(detail=True, methods=['post'], url_path='create-requests')
    def create_requests(self, request, pk=None):
        round_obj = self.get_object()
        items = request.data.get('requests', [])
        created = 0
        for item in items:
            _, was_created = FeedbackRequest.objects.get_or_create(
                feedback_round=round_obj,
                recipient_id=item['recipient'],
                feedback_giver_id=item['feedback_giver'],
                defaults={'giver_type': item.get('giver_type', 'peer')},
            )
            if was_created:
                created += 1
        return Response({'created': created})


class FeedbackRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackRequestSerializer

    def get_queryset(self):
        qs = FeedbackRequest.objects.select_related(
            'recipient', 'feedback_giver', 'feedback_round'
        ).order_by('-created_at')
        if self.request.user.is_admin or self.request.user.is_manager:
            return qs
        return qs.filter(feedback_giver=self.request.user)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        qs = self.get_queryset().filter(feedback_giver=request.user)
        pending = qs.filter(status='pending').count()
        submitted = qs.filter(status='submitted').count()
        serializer = self.get_serializer(qs, many=True)
        return Response({
            'requests': serializer.data,
            'pending': pending,
            'submitted': submitted,
        })

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        feedback_request = self.get_object()
        if feedback_request.feedback_giver != request.user:
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        if feedback_request.status == 'submitted':
            return Response({'detail': 'Already submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        rating_fields = [
            'communication', 'leadership', 'teamwork',
            'reliability', 'initiative', 'problem_solving',
        ]
        defaults = {field: request.data.get(field) for field in rating_fields}
        defaults.update({
            'strengths': request.data.get('strengths', ''),
            'areas_for_improvement': request.data.get('areas_for_improvement', ''),
            'additional_comments': request.data.get('additional_comments', ''),
            'is_anonymous': request.data.get('is_anonymous', False),
        })
        feedback, _ = Feedback.objects.update_or_create(
            request=feedback_request,
            defaults=defaults,
        )
        feedback_request.status = 'submitted'
        feedback_request.submitted_at = timezone.now()
        feedback_request.save()
        return Response(FeedbackSerializer(feedback).data)

    @action(detail=False, methods=['get'], url_path='employee-summary')
    def employee_summary(self, request):
        from django.db.models import Avg
        from django.shortcuts import get_object_or_404

        employee_id = request.query_params.get('employee')
        round_id = request.query_params.get('round')
        if not employee_id:
            return Response({'detail': 'employee query param required.'}, status=400)

        employee = get_object_or_404(Employee, pk=employee_id)
        requests_qs = FeedbackRequest.objects.filter(
            recipient=employee, status='submitted'
        ).select_related('feedback_round', 'feedback_giver')
        if round_id:
            requests_qs = requests_qs.filter(feedback_round_id=round_id)

        feedbacks = Feedback.objects.filter(request__in=requests_qs)
        averages = {}
        for field in [
            'communication', 'leadership', 'teamwork',
            'reliability', 'initiative', 'problem_solving',
        ]:
            val = feedbacks.aggregate(v=Avg(field))['v']
            averages[field] = round(val, 2) if val is not None else None

        return Response({
            'employee': {'id': employee.id, 'full_name': employee.full_name},
            'requests': FeedbackRequestSerializer(
                requests_qs, many=True, context=self.get_serializer_context()
            ).data,
            'averages': averages,
            'response_count': feedbacks.count(),
        })


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().order_by('-created_at')
    serializer_class = FeedbackSerializer


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all().order_by('category', 'name')
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeSkillViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = EmployeeSkillSerializer

    def get_queryset(self):
        qs = EmployeeSkill.objects.select_related('employee', 'skill')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class TrainingCourseViewSet(viewsets.ModelViewSet):
    queryset = TrainingCourse.objects.all().order_by('-start_date')
    serializer_class = TrainingCourseSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TrainingRecordViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = TrainingRecordSerializer

    def get_queryset(self):
        qs = TrainingRecord.objects.select_related('employee', 'course').order_by('-enrolled_date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all().order_by('name')
    serializer_class = CertificationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeCertificationViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = EmployeeCertificationSerializer

    def get_queryset(self):
        qs = EmployeeCertification.objects.select_related('employee', 'certification')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class DevelopmentPlanViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DevelopmentPlanSerializer

    def get_queryset(self):
        qs = DevelopmentPlan.objects.select_related('employee').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class ExitProcessViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ExitProcessSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return ExitProcess.objects.select_related('employee').order_by('-created_at')


class ExitChecklistViewSet(viewsets.ModelViewSet):
    serializer_class = ExitChecklistSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ExitChecklist.objects.select_related('exit_process').order_by('exit_process', 'created_at')
        exit_id = self.request.query_params.get('exit_process')
        if exit_id:
            qs = qs.filter(exit_process_id=exit_id)
        return qs


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all().order_by('-created_at')
    serializer_class = AssetSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class AssetAssignmentViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = AssetAssignment.objects.select_related('asset', 'employee').order_by('-assignment_date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.filter(is_active=True).order_by('start_time')
    serializer_class = ShiftSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class ShiftAssignmentViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ShiftAssignmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ShiftAssignment.objects.select_related('employee', 'shift', 'department')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class ExpenseViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Expense.objects.select_related('employee', 'category').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        expense = self.get_object()
        expense.status = 'approved'
        expense.approved_date = timezone.now()
        expense.save()
        log_action(request, 'approve', 'Expense', expense.id, expense.description, 'Expense approved')
        return Response(ExpenseSerializer(expense).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        expense = self.get_object()
        expense.status = 'rejected'
        expense.rejection_reason = request.data.get('reason', '')
        expense.save()
        log_action(request, 'reject', 'Expense', expense.id, expense.description, 'Expense rejected')
        return Response(ExpenseSerializer(expense).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return AuditLog.objects.select_related('user').order_by('-timestamp')


class BenefitViewSet(viewsets.ModelViewSet):
    queryset = Benefit.objects.filter(is_active=True).order_by('name')
    serializer_class = BenefitSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeBenefitViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = EmployeeBenefitSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = EmployeeBenefit.objects.select_related('employee', 'benefit')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class LeavePolicyViewSet(viewsets.ModelViewSet):
    queryset = LeavePolicy.objects.filter(is_active=True).order_by('name')
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class LeavePolicyAllocationViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = LeavePolicyAllocationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = LeavePolicyAllocation.objects.select_related('employee', 'policy')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class DisciplineViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DisciplineSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = Discipline.objects.select_related('employee').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class DisciplineAppealViewSet(viewsets.ModelViewSet):
    queryset = DisciplineAppeal.objects.all().order_by('-created_at')
    serializer_class = DisciplineAppealSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class KinViewSet(EmployeeQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = KinSerializer

    def get_queryset(self):
        qs = Kin.objects.select_related('employee')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all().order_by('-created_at')
    serializer_class = SurveySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'available', 'submit', 'results'):
            return [IsAuthenticated()]
        return [IsAdminOrManagerOrReadOnly()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        data['questions'] = SurveyQuestionSerializer(
            instance.questions.all().order_by('order'), many=True
        ).data
        return Response(data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        today = timezone.now().date()
        qs = Survey.objects.filter(
            status='active', start_date__lte=today, end_date__gte=today
        ).order_by('-created_at')
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        survey = self.get_object()
        answers = request.data.get('answers', [])
        if not answers:
            return Response({'detail': 'No answers provided.'}, status=status.HTTP_400_BAD_REQUEST)

        employee = None
        if not survey.is_anonymous:
            try:
                employee = Employee.objects.get(email=request.user.email)
            except Employee.DoesNotExist:
                return Response({'detail': 'Employee profile required.'}, status=400)

        for ans in answers:
            question_id = ans.get('question_id')
            if not question_id:
                continue
            SurveyResponse.objects.create(
                survey=survey,
                respondent=employee,
                question_id=question_id,
                response_text=ans.get('response_text', ''),
                response_rating=ans.get('response_rating'),
                response_selected=ans.get('response_selected', ''),
            )
        return Response({'detail': 'Survey submitted successfully.'})

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        from django.db.models import Avg, Count

        survey = self.get_object()
        question_results = []
        for question in survey.questions.all().order_by('order'):
            responses = SurveyResponse.objects.filter(survey=survey, question=question)
            item = {
                'question_id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'total_responses': responses.count(),
            }
            if question.question_type == 'rating':
                item['average_rating'] = round(
                    responses.aggregate(v=Avg('response_rating'))['v'] or 0, 2
                )
                item['distribution'] = list(
                    responses.values('response_rating').annotate(count=Count('id'))
                )
            elif question.question_type == 'text':
                item['text_responses'] = list(
                    responses.values_list('response_text', flat=True)[:100]
                )
            else:
                item['selected_responses'] = list(
                    responses.values_list('response_selected', flat=True)[:100]
                )
            question_results.append(item)

        unique_responders = SurveyResponse.objects.filter(survey=survey).values(
            'respondent'
        ).distinct().count()

        return Response({
            'survey': self.get_serializer(survey).data,
            'total_responders': unique_responders,
            'questions': question_results,
        })


class SurveyQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = SurveyQuestionSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = SurveyQuestion.objects.select_related('survey').order_by('survey', 'order')
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            qs = qs.filter(survey_id=survey_id)
        return qs


class SurveyResponseViewSet(viewsets.ModelViewSet):
    serializer_class = SurveyResponseSerializer

    def get_queryset(self):
        qs = SurveyResponse.objects.select_related('survey', 'question').order_by('-created_at')
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            qs = qs.filter(survey_id=survey_id)
        return qs
