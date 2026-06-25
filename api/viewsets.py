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

from .approval_integration import (
    process_expense_decision,
    process_leave_decision,
    process_recruitment_decision,
    start_expense_approval,
    start_leave_approval,
)
from .audit import log_action
from .mixins import AuditedModelViewSet, EmployeeQuerysetMixin
from .notifications import (
    notify_appraisal_approved,
    notify_appraisal_submitted,
    notify_application_status,
    notify_benefit_enrollment_decision,
    notify_benefit_enrollment_submitted,
    notify_discipline_appeal_decision,
    notify_discipline_appeal_submitted,
    notify_expense_decision,
    notify_expense_submitted,
    notify_leave_decision,
    notify_leave_submitted,
)
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


class EmployeeViewSet(AuditedModelViewSet):
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
        log_action(
            request, 'update', 'Employee', employee.id, employee.full_name,
            f'Employee terminated: {employee.exit_reason}',
        )
        from integrations.services import dispatch_webhook
        dispatch_webhook('employee.terminated', {
            'id': employee.id,
            'email': employee.email,
            'full_name': employee.full_name,
            'exit_reason': employee.exit_reason,
        })
        return Response(EmployeeSerializer(employee, context={'request': request}).data)

    def perform_create(self, serializer):
        employee = serializer.save()
        from integrations.services import dispatch_webhook
        dispatch_webhook('employee.created', {
            'id': employee.id,
            'email': employee.email,
            'full_name': employee.full_name,
            'department_id': employee.department_id,
            'job_title': employee.job_title,
        })


class DepartmentViewSet(AuditedModelViewSet):
    queryset = Department.objects.select_related('parent').all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    @action(detail=False, methods=['get'])
    def org_chart(self, request):
        from departments.services import build_org_chart
        return Response(build_org_chart())


class LeaveViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
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
        notify_leave_submitted(leave)
        start_leave_approval(leave, self.request.user)
        from integrations.services import dispatch_webhook
        dispatch_webhook('leave.submitted', {
            'id': leave.id,
            'employee_id': leave.employee_id,
            'employee_name': leave.employee.full_name,
            'leave_type': leave.leave_type,
            'start_date': str(leave.start_date),
            'end_date': str(leave.end_date),
            'duration': leave.duration,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'detail': 'Leave is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        outcome = process_leave_decision(request, leave, True, request.data.get('comment', ''))
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if outcome['result'] == 'approved':
            notify_leave_decision(leave, 'approved')
        elif outcome['result'] == 'rejected':
            notify_leave_decision(leave, 'rejected')
        return Response(LeaveSerializer(leave, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'detail': 'Leave is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        outcome = process_leave_decision(
            request, leave, False, request.data.get('reason', request.data.get('comment', '')),
        )
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        notify_leave_decision(leave, 'rejected')
        return Response(LeaveSerializer(leave, context={'request': request}).data)


class LeaveBalanceViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
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


class AttendanceViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
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


class JobPostingViewSet(AuditedModelViewSet):
    queryset = JobPosting.objects.all().order_by('-posted_on')
    serializer_class = JobPostingSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class ApplicationViewSet(AuditedModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Application.objects.select_related('job').order_by('-applied_on')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs

    def perform_update(self, serializer):
        previous_status = serializer.instance.get_status_display()
        old_status = serializer.instance.status
        application = serializer.save()
        if old_status != application.status:
            notify_application_status(application, previous_status)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        application = self.get_object()
        outcome = process_recruitment_decision(request, application, True, request.data.get('comment', ''))
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if application.email and outcome['result'] == 'approved':
            notify_application_status(application, application.get_status_display())
        return Response(ApplicationSerializer(application, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        application = self.get_object()
        outcome = process_recruitment_decision(
            request, application, False, request.data.get('reason', request.data.get('comment', '')),
        )
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if application.email:
            notify_application_status(application, 'Pending')
        return Response(ApplicationSerializer(application, context={'request': request}).data)


class SalaryViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
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


class PerformanceGoalViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = PerformanceGoalSerializer

    def get_queryset(self):
        qs = PerformanceGoal.objects.select_related('employee').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        serializer.save(set_by=self.request.user)


class PerformanceAppraisalViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
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
        log_action(
            request, 'update', 'PerformanceAppraisal', appraisal.id, str(appraisal),
            'Appraisal submitted for review',
        )
        submitted_by = request.user.get_full_name() or request.user.username
        notify_appraisal_submitted(appraisal, submitted_by)
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        appraisal = self.get_object()
        appraisal.status = 'approved'
        appraisal.approved_at = timezone.now()
        appraisal.save()
        log_action(
            request, 'approve', 'PerformanceAppraisal', appraisal.id, str(appraisal),
            'Appraisal approved',
        )
        notify_appraisal_approved(appraisal)
        return Response(PerformanceAppraisalSerializer(appraisal).data)


class FeedbackRoundViewSet(AuditedModelViewSet):
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


class FeedbackRequestViewSet(AuditedModelViewSet):
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


class FeedbackViewSet(AuditedModelViewSet):
    queryset = Feedback.objects.all().order_by('-created_at')
    serializer_class = FeedbackSerializer


class SkillViewSet(AuditedModelViewSet):
    queryset = Skill.objects.all().order_by('category', 'name')
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeSkillViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmployeeSkillSerializer

    def get_queryset(self):
        qs = EmployeeSkill.objects.select_related('employee', 'skill')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class TrainingCourseViewSet(AuditedModelViewSet):
    queryset = TrainingCourse.objects.all().order_by('-start_date')
    serializer_class = TrainingCourseSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TrainingRecordViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = TrainingRecordSerializer

    def get_queryset(self):
        qs = TrainingRecord.objects.select_related('employee', 'course').order_by('-enrolled_date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class CertificationViewSet(AuditedModelViewSet):
    queryset = Certification.objects.all().order_by('name')
    serializer_class = CertificationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeCertificationViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmployeeCertificationSerializer

    def get_queryset(self):
        qs = EmployeeCertification.objects.select_related('employee', 'certification')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class DevelopmentPlanViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = DevelopmentPlanSerializer

    def get_queryset(self):
        qs = DevelopmentPlan.objects.select_related('employee').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class ExitProcessViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = ExitProcessSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return ExitProcess.objects.select_related('employee').order_by('-created_at')


class ExitChecklistViewSet(AuditedModelViewSet):
    serializer_class = ExitChecklistSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ExitChecklist.objects.select_related('exit_process').order_by('exit_process', 'created_at')
        exit_id = self.request.query_params.get('exit_process')
        if exit_id:
            qs = qs.filter(exit_process_id=exit_id)
        return qs


class AssetViewSet(AuditedModelViewSet):
    queryset = Asset.objects.all().order_by('-created_at')
    serializer_class = AssetSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class AssetAssignmentViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = AssetAssignment.objects.select_related('asset', 'employee').order_by('-assignment_date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class ShiftViewSet(AuditedModelViewSet):
    queryset = Shift.objects.filter(is_active=True).order_by('start_time')
    serializer_class = ShiftSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class ShiftAssignmentViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = ShiftAssignmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ShiftAssignment.objects.select_related('employee', 'shift', 'department')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class ExpenseCategoryViewSet(AuditedModelViewSet):
    queryset = ExpenseCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class ExpenseViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = ExpenseSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Expense.objects.select_related('employee', 'category').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        expense = serializer.save()
        if expense.status in ('submitted', 'approved'):
            notify_expense_submitted(expense)
            start_expense_approval(expense, self.request.user)

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        expense = serializer.save()
        if previous_status != 'submitted' and expense.status == 'submitted':
            notify_expense_submitted(expense)
            start_expense_approval(expense, self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        expense = self.get_object()
        outcome = process_expense_decision(request, expense, True, request.data.get('comment', ''))
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if outcome['result'] == 'approved':
            notify_expense_decision(expense, 'approved')
        elif outcome['result'] == 'rejected':
            notify_expense_decision(expense, 'rejected')
        return Response(ExpenseSerializer(expense, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        expense = self.get_object()
        outcome = process_expense_decision(
            request, expense, False, request.data.get('reason', request.data.get('comment', '')),
        )
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        notify_expense_decision(expense, 'rejected')
        return Response(ExpenseSerializer(expense, context={'request': request}).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return AuditLog.objects.select_related('user').order_by('-timestamp')


class BenefitViewSet(AuditedModelViewSet):
    queryset = Benefit.objects.filter(is_active=True).order_by('name')
    serializer_class = BenefitSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeBenefitViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmployeeBenefitSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = EmployeeBenefit.objects.select_related('employee', 'benefit')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        enrollment = serializer.save()
        if enrollment.status == 'pending':
            notify_benefit_enrollment_submitted(enrollment)

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        enrollment = serializer.save()
        if previous_status == 'pending' and enrollment.status == 'active':
            notify_benefit_enrollment_decision(enrollment, 'approved')
        elif previous_status == 'pending' and enrollment.status == 'terminated':
            notify_benefit_enrollment_decision(enrollment, 'rejected')


class LeavePolicyViewSet(AuditedModelViewSet):
    queryset = LeavePolicy.objects.filter(is_active=True).order_by('name')
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class LeavePolicyAllocationViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = LeavePolicyAllocationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = LeavePolicyAllocation.objects.select_related('employee', 'policy')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrManager])
    def sync(self, request):
        from leave_policies.services import sync_all_employees, sync_employee_allocations

        employee_id = request.data.get('employee')
        year = request.data.get('year')
        if employee_id:
            employee = Employee.objects.get(pk=employee_id)
            results = sync_employee_allocations(employee, year)
            return Response({'employee': employee.id, 'synced': len(results), 'details': results})
        summary = sync_all_employees(year)
        return Response(summary)


class DisciplineViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = DisciplineSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = Discipline.objects.select_related('employee').order_by('-created_at')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class DisciplineAppealViewSet(AuditedModelViewSet):
    queryset = DisciplineAppeal.objects.all().order_by('-created_at')
    serializer_class = DisciplineAppealSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def perform_create(self, serializer):
        appeal = serializer.save()
        notify_discipline_appeal_submitted(appeal)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        appeal = self.get_object()
        appeal.status = 'approved'
        appeal.review_date = timezone.now().date()
        appeal.review_notes = request.data.get('review_notes', appeal.review_notes)
        appeal.save()
        log_action(
            request, 'approve', 'DisciplineAppeal', appeal.id, str(appeal),
            'Discipline appeal approved',
        )
        notify_discipline_appeal_decision(appeal, 'approved')
        return Response(DisciplineAppealSerializer(appeal).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        appeal = self.get_object()
        appeal.status = 'rejected'
        appeal.review_date = timezone.now().date()
        appeal.review_notes = request.data.get('review_notes', appeal.review_notes)
        appeal.save()
        log_action(
            request, 'reject', 'DisciplineAppeal', appeal.id, str(appeal),
            'Discipline appeal rejected',
        )
        notify_discipline_appeal_decision(appeal, 'rejected')
        return Response(DisciplineAppealSerializer(appeal).data)


class KinViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = KinSerializer

    def get_queryset(self):
        qs = Kin.objects.select_related('employee')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs


class SurveyViewSet(AuditedModelViewSet):
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


class SurveyQuestionViewSet(AuditedModelViewSet):
    serializer_class = SurveyQuestionSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = SurveyQuestion.objects.select_related('survey').order_by('survey', 'order')
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            qs = qs.filter(survey_id=survey_id)
        return qs


class SurveyResponseViewSet(AuditedModelViewSet):
    serializer_class = SurveyResponseSerializer

    def get_queryset(self):
        qs = SurveyResponse.objects.select_related('survey', 'question').order_by('-created_at')
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            qs = qs.filter(survey_id=survey_id)
        return qs


class NotificationViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'patch', 'head', 'options', 'post']

    def get_serializer_class(self):
        from .serializers_phase2 import NotificationSerializer
        return NotificationSerializer

    def get_queryset(self):
        return self.request.user.notifications.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({'marked_read': updated})


class HRDocumentViewSet(AuditedModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        from .serializers_phase2 import HRDocumentSerializer
        return HRDocumentSerializer

    def get_queryset(self):
        from documents.models import HRDocument
        qs = HRDocument.objects.filter(is_active=True).select_related('employee', 'uploaded_by')
        if not self.request.user.is_admin:
            try:
                employee = Employee.objects.get(email=self.request.user.email)
                qs = qs.filter(Q(employee=employee) | Q(employee__isnull=True))
            except Employee.DoesNotExist:
                qs = qs.filter(employee__isnull=True)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs.order_by('-created_at')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminOrManagerOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ApprovalWorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    def get_serializer_class(self):
        from .serializers_phase2 import ApprovalWorkflowSerializer
        return ApprovalWorkflowSerializer

    def get_queryset(self):
        from workflows.models import ApprovalWorkflow
        return ApprovalWorkflow.objects.filter(is_active=True).prefetch_related('steps')

    def get_permissions(self):
        return [IsAdminOrManagerOrReadOnly()]


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    def get_serializer_class(self):
        from .serializers_phase2 import ApprovalRequestSerializer
        return ApprovalRequestSerializer

    def get_queryset(self):
        from workflows.models import ApprovalRequest
        from workflows.services import get_pending_for_user

        scope = self.request.query_params.get('scope', 'mine')
        if scope == 'all' and self.request.user.is_admin:
            return ApprovalRequest.objects.select_related('workflow', 'content_type').prefetch_related('decisions')
        return get_pending_for_user(self.request.user)


class APIKeyViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        return [IsAdmin()]

    def get_serializer_class(self):
        from .integrations_serializers import APIKeyCreateSerializer, APIKeySerializer
        if self.action == 'create':
            return APIKeyCreateSerializer
        return APIKeySerializer

    def get_queryset(self):
        from integrations.models import APIKey
        return APIKey.objects.select_related('user').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        from integrations.models import APIKey
        from .integrations_serializers import APIKeyCreateSerializer, APIKeySerializer

        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance, raw_key = APIKey.generate(request.user, serializer.validated_data['name'])
        data = APIKeySerializer(instance).data
        data['api_key'] = raw_key
        return Response(data, status=status.HTTP_201_CREATED)


class WebhookEndpointViewSet(AuditedModelViewSet):
    def get_serializer_class(self):
        from .integrations_serializers import WebhookDeliverySerializer, WebhookEndpointSerializer
        if self.action == 'deliveries':
            return WebhookDeliverySerializer
        return WebhookEndpointSerializer

    def get_queryset(self):
        from integrations.models import WebhookEndpoint
        return WebhookEndpoint.objects.order_by('name')

    def get_permissions(self):
        return [IsAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        endpoint = self.get_object()
        from integrations.models import WebhookDelivery
        qs = WebhookDelivery.objects.filter(endpoint=endpoint).order_by('-delivered_at')[:50]
        from .integrations_serializers import WebhookDeliverySerializer
        return Response(WebhookDeliverySerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def events(self, request):
        from integrations.models import WEBHOOK_EVENTS
        return Response({'events': WEBHOOK_EVENTS})
