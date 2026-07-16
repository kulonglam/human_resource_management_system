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
from accounts.models import AuditLog, CustomUser, Role
from assets.models import Asset, AssetAssignment
from attendance.models import Attendance, OvertimeRecord, PublicHoliday, Timesheet
from benefits.models import Benefit, EmployeeBenefit
from departments.models import Department
from discipline.models import Discipline, DisciplineAppeal
from employees.models import Employee, EmploymentContract, EmploymentHistory, JobGrade, Position
from exits.models import ExitChecklist, ExitProcess
from expenses.models import Expense, ExpenseCategory
from kin.models import Kin
from leave_policies.models import LeavePolicy, LeavePolicyAllocation
from leaves.models import Leave, LeaveBalance
from payroll.models import PayrollRun, Salary
from payroll.utils import generate_salary_slip_pdf
from performance.models import (
    Feedback,
    FeedbackRequest,
    FeedbackRound,
    PerformanceAppraisal,
    PerformanceGoal,
)
from recruitment.models import (
    Application,
    ApplicationNote,
    ApplicationScorecard,
    HireOnboarding,
    HiringTeamMember,
    Interview,
    JobOffer,
    JobPipelineStage,
    JobPosting,
    OfferTemplate,
    ScorecardCriterion,
)
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
from .permissions import (
    CanApproveAttendance,
    CanManageReports,
    IsAdmin,
    IsAdminOrManager,
    IsAdminOrManagerOrReadOnly,
    IsAdminOrReadOnly,
    IsPayrollManager,
    IsPayrollUser,
    RequiresMFAForPayroll,
)
from .serializers_reports import ReportSnapshotSerializer, SavedReportSerializer, ScheduledReportSerializer
from .serializers import (
    AuditLogSerializer,
    DepartmentSerializer,
    EmployeeSerializer,
    EmployeeTerminateSerializer,
    EmploymentContractSerializer,
    EmploymentHistorySerializer,
    JobGradeSerializer,
    PositionSerializer,
)
from .serializers_hr import (
    ApplicationNoteSerializer,
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
    InterviewSerializer,
    JobPostingSerializer,
    KinSerializer,
    LeaveBalanceSerializer,
    LeavePolicyAllocationSerializer,
    LeavePolicySerializer,
    LeaveSerializer,
    OvertimeRecordSerializer,
    PerformanceAppraisalSerializer,
    PerformanceGoalSerializer,
    PayrollRunSerializer,
    PublicHolidaySerializer,
    SalarySerializer,
    ShiftAssignmentSerializer,
    ShiftSerializer,
    SkillSerializer,
    SurveyQuestionSerializer,
    SurveyResponseSerializer,
    SurveySerializer,
    TimesheetSerializer,
    TrainingCourseSerializer,
    TrainingRecordSerializer,
)
from .recruitment_enterprise import (
    ApplicationScorecardSerializer,
    ApplicationScorecardWriteSerializer,
    CompleteOnboardingSerializer,
    HireOnboardingSerializer,
    HiringTeamMemberSerializer,
    JobOfferCreateSerializer,
    JobOfferSerializer,
    JobPipelineStageSerializer,
    OfferTemplateSerializer,
    ScorecardCriterionSerializer,
)
from recruitment.services import (
    build_offer_from_template,
    create_hire_onboarding,
    complete_hire_onboarding,
    sync_application_stage,
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
        from accounts.access_control import can_view_sensitive_data
        from api.sensitive_access import log_sensitive_employee_access

        if can_view_sensitive_data(request.user):
            log_sensitive_employee_access(request, employee)
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
        if getattr(self.request.user, 'organization_id', None) and not employee.organization_id:
            employee.organization_id = self.request.user.organization_id
            employee.save(update_fields=['organization_id'])
        from integrations.services import dispatch_webhook
        dispatch_webhook('employee.created', {
            'id': employee.id,
            'email': employee.email,
            'full_name': employee.full_name,
            'department_id': employee.department_id,
            'job_title': employee.job_title,
        })


class JobGradeViewSet(AuditedModelViewSet):
    queryset = JobGrade.objects.all()
    serializer_class = JobGradeSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class PositionViewSet(AuditedModelViewSet):
    queryset = Position.objects.select_related('department', 'grade', 'reports_to').all()
    serializer_class = PositionSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmploymentContractViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmploymentContractSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = EmploymentContract.objects.select_related('employee').all()
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs


class EmploymentHistoryViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmploymentHistorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = EmploymentHistory.objects.select_related('employee').all()
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


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
            if balance.available_days < leave.working_days:
                leave.delete()
                raise serializers.ValidationError(
                    f'Insufficient leave balance. Available: {balance.available_days} days.'
                )
            balance.pending_days += leave.working_days
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

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrManager])
    def accrue(self, request):
        from leaves.services import accrue_monthly_balances

        result = accrue_monthly_balances(request.data.get('year'), request.data.get('month'))
        return Response(result)

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def carry_forward(self, request):
        from leaves.services import carry_forward_balances

        from_year = int(request.data.get('from_year', timezone.now().year - 1))
        to_year = int(request.data.get('to_year', timezone.now().year))
        return Response(carry_forward_balances(from_year, to_year))


class AttendanceViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            'employee', 'approved_by', 'shift_assignment__shift',
        ).order_by('-date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        approval_status = self.request.query_params.get('approval_status')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if approval_status:
            qs = qs.filter(approval_status=approval_status)
        return qs

    def perform_create(self, serializer):
        from attendance.services import derive_attendance_status, match_shift_for_date

        attendance = serializer.save()
        assignment = match_shift_for_date(attendance.employee, attendance.date)
        if assignment:
            attendance.shift_assignment = assignment
        if attendance.time_in or attendance.time_out:
            attendance.status = derive_attendance_status(attendance)
        attendance.save()

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        attendance = self.get_object()
        if attendance.approval_status not in ('draft', 'rejected'):
            return Response({'detail': 'Attendance is not in a submittable state.'}, status=status.HTTP_400_BAD_REQUEST)
        attendance.approval_status = 'submitted'
        attendance.save(update_fields=['approval_status'])
        return Response(AttendanceSerializer(attendance, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def approve(self, request, pk=None):
        attendance = self.get_object()
        if attendance.approval_status != 'submitted':
            return Response({'detail': 'Only submitted attendance can be approved.'}, status=status.HTTP_400_BAD_REQUEST)
        attendance.approval_status = 'approved'
        attendance.approved_by = request.user
        attendance.approved_at = timezone.now()
        attendance.save()
        log_action(request, 'approve', 'Attendance', attendance.id, str(attendance), 'Attendance approved')
        return Response(AttendanceSerializer(attendance, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def reject(self, request, pk=None):
        attendance = self.get_object()
        if attendance.approval_status != 'submitted':
            return Response({'detail': 'Only submitted attendance can be rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        attendance.approval_status = 'rejected'
        attendance.approved_by = request.user
        attendance.approved_at = timezone.now()
        attendance.notes = request.data.get('reason', attendance.notes)
        attendance.save()
        log_action(request, 'reject', 'Attendance', attendance.id, str(attendance), 'Attendance rejected')
        return Response(AttendanceSerializer(attendance, context={'request': request}).data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], permission_classes=[CanApproveAttendance])
    def import_csv(self, request):
        from attendance.services import import_attendance_csv
        from api.uploads import validate_upload

        upload = request.FILES.get('file')
        if not upload:
            return Response({'detail': 'CSV file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_upload(upload, kind='csv')
        except Exception as exc:
            detail = getattr(exc, 'detail', str(exc))
            return Response(detail if isinstance(detail, dict) else {'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
        result = import_attendance_csv(upload)
        log_action(request, 'create', 'Attendance', None, 'Attendance import', f'Imported {result["created"]} created, {result["updated"]} updated')
        return Response(result)


class PublicHolidayViewSet(AuditedModelViewSet):
    queryset = PublicHoliday.objects.all()
    serializer_class = PublicHolidaySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class TimesheetViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = TimesheetSerializer

    def get_queryset(self):
        qs = Timesheet.objects.select_related('employee', 'approved_by').order_by('-date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        timesheet = self.get_object()
        if timesheet.status not in ('draft', 'rejected'):
            return Response({'detail': 'Timesheet is not in a submittable state.'}, status=status.HTTP_400_BAD_REQUEST)
        timesheet.status = 'submitted'
        timesheet.submitted_at = timezone.now()
        timesheet.save()
        return Response(TimesheetSerializer(timesheet, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def approve(self, request, pk=None):
        from attendance.services import sync_timesheet_to_attendance

        timesheet = self.get_object()
        if timesheet.status != 'submitted':
            return Response({'detail': 'Only submitted timesheets can be approved.'}, status=status.HTTP_400_BAD_REQUEST)
        timesheet.status = 'approved'
        timesheet.approved_by = request.user
        timesheet.approved_at = timezone.now()
        timesheet.save()
        sync_timesheet_to_attendance(timesheet)
        log_action(request, 'approve', 'Timesheet', timesheet.id, str(timesheet), 'Timesheet approved')
        return Response(TimesheetSerializer(timesheet, context={'request': request}).data)


class OvertimeRecordViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = OvertimeRecordSerializer

    def get_queryset(self):
        qs = OvertimeRecord.objects.select_related('employee', 'approved_by').order_by('-date')
        if not self.request.user.is_admin:
            qs = self.filter_by_accessible_employees(qs)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def approve(self, request, pk=None):
        record = self.get_object()
        if record.status != 'pending':
            return Response({'detail': 'Overtime record is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        record.status = 'approved'
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()
        log_action(request, 'approve', 'OvertimeRecord', record.id, str(record), 'Overtime approved')
        return Response(OvertimeRecordSerializer(record, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def reject(self, request, pk=None):
        record = self.get_object()
        if record.status != 'pending':
            return Response({'detail': 'Overtime record is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        record.status = 'rejected'
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()
        return Response(OvertimeRecordSerializer(record, context={'request': request}).data)


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
            if application.status == 'hired' and not application.hired_at:
                application.hired_at = timezone.now()
                application.save(update_fields=['hired_at'])
            notify_application_status(application, previous_status)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        application = self.get_object()
        outcome = process_recruitment_decision(request, application, True, request.data.get('comment', ''))
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        application.refresh_from_db()
        if application.email and outcome['result'] in ('approved', 'advanced'):
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
        application.refresh_from_db()
        if application.email:
            notify_application_status(application, application.get_status_display())
        return Response(ApplicationSerializer(application, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def move_stage(self, request, pk=None):
        application = self.get_object()
        stage_id = request.data.get('stage_id')
        if not stage_id:
            return Response({'detail': 'stage_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        stage = JobPipelineStage.objects.filter(pk=stage_id, job=application.job).first()
        if not stage:
            return Response({'detail': 'Invalid stage for this job.'}, status=status.HTTP_400_BAD_REQUEST)
        sync_application_stage(application, stage)
        if stage.stage_type == 'hired':
            create_hire_onboarding(application)
        return Response(ApplicationSerializer(application, context={'request': request}).data)


class ApplicationNoteViewSet(AuditedModelViewSet):
    serializer_class = ApplicationNoteSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ApplicationNote.objects.select_related('application', 'author')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class InterviewViewSet(AuditedModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = Interview.objects.select_related('application', 'created_by')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs

    def perform_create(self, serializer):
        interview = serializer.save(created_by=self.request.user)
        application = interview.application
        stage = application.job.pipeline_stages.filter(key='interviewed').first()
        if stage:
            sync_application_stage(application, stage)
        elif application.status in ('received', 'shortlisted'):
            application.status = 'interviewed'
            application.save(update_fields=['status'])


class JobPipelineStageViewSet(AuditedModelViewSet):
    serializer_class = JobPipelineStageSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = JobPipelineStage.objects.select_related('job')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class HiringTeamMemberViewSet(AuditedModelViewSet):
    serializer_class = HiringTeamMemberSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = HiringTeamMember.objects.select_related('user', 'job')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class ScorecardCriterionViewSet(AuditedModelViewSet):
    serializer_class = ScorecardCriterionSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ScorecardCriterion.objects.select_related('job')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class ApplicationScorecardViewSet(AuditedModelViewSet):
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ApplicationScorecardWriteSerializer
        return ApplicationScorecardSerializer

    def get_queryset(self):
        qs = ApplicationScorecard.objects.select_related('reviewer', 'application').prefetch_related('ratings__criterion')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs


class OfferTemplateViewSet(AuditedModelViewSet):
    queryset = OfferTemplate.objects.filter(is_active=True).order_by('name')
    serializer_class = OfferTemplateSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class JobOfferViewSet(AuditedModelViewSet):
    serializer_class = JobOfferSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = JobOffer.objects.select_related('application', 'template', 'created_by')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], url_path='from-template')
    def from_template(self, request):
        serializer = JobOfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        application = data['application']
        offer = build_offer_from_template(
            data['template'],
            application,
            request.user,
            salary=data['salary'],
            start_date=data['start_date'],
            currency=data.get('currency', 'UGX'),
            job_title=data.get('job_title') or application.job.title,
            department=data.get('department') or application.job.department,
        )
        offer.save()
        return Response(JobOfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        offer = self.get_object()
        offer.status = 'pending_approval'
        offer.save(update_fields=['status', 'updated_at'])
        return Response(JobOfferSerializer(offer).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        offer = self.get_object()
        if offer.status != 'pending_approval':
            return Response({'detail': 'Offer is not pending approval.'}, status=status.HTTP_400_BAD_REQUEST)
        offer.status = 'approved'
        offer.save(update_fields=['status', 'updated_at'])
        return Response(JobOfferSerializer(offer).data)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        offer = self.get_object()
        if offer.status not in ('approved', 'draft'):
            return Response({'detail': 'Offer must be approved before sending.'}, status=status.HTTP_400_BAD_REQUEST)
        offer.status = 'sent'
        offer.sent_at = timezone.now()
        offer.save(update_fields=['status', 'sent_at', 'updated_at'])
        stage = offer.application.job.pipeline_stages.filter(key='offer').first()
        if stage:
            sync_application_stage(offer.application, stage)
        return Response(JobOfferSerializer(offer).data)


class HireOnboardingViewSet(AuditedModelViewSet):
    serializer_class = HireOnboardingSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    http_method_names = ['get', 'patch', 'head', 'options', 'post']

    def get_queryset(self):
        qs = HireOnboarding.objects.select_related('application', 'employee').order_by('-created_at')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        onboarding = self.get_object()
        if onboarding.status == 'completed':
            return Response({'detail': 'Onboarding already completed.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompleteOnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = complete_hire_onboarding(onboarding, request.user, serializer.validated_data)
        onboarding.refresh_from_db()
        return Response({
            'onboarding': HireOnboardingSerializer(onboarding).data,
            'employee_id': employee.id,
        })


class PayrollRunViewSet(AuditedModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsPayrollUser(), RequiresMFAForPayroll()]
        return [IsPayrollManager(), RequiresMFAForPayroll()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        payroll_run = self.get_object()
        if payroll_run.status != 'draft':
            return Response(
                {'detail': 'Approved or paid payroll runs are locked.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        payroll_run = self.get_object()
        if payroll_run.status != 'draft':
            return Response({'detail': 'Only draft payroll runs can be approved.'}, status=400)
        if not payroll_run.salary_records.exists():
            return Response({'detail': 'Add salary records before approving this run.'}, status=400)
        payroll_run.salary_records.update(status='approved', is_paid=False)
        payroll_run.status = 'approved'
        payroll_run.approved_by = request.user
        payroll_run.approved_at = timezone.now()
        payroll_run.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        log_action(request, 'approve', 'PayrollRun', payroll_run.id, str(payroll_run))
        return Response(PayrollRunSerializer(payroll_run).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def mark_paid(self, request, pk=None):
        payroll_run = self.get_object()
        if payroll_run.status != 'approved':
            return Response({'detail': 'Only approved payroll runs can be marked paid.'}, status=400)
        paid_at = timezone.now()
        payroll_run.salary_records.update(
            status='paid', is_paid=True, paid_on=paid_at.date(), updated_at=paid_at,
        )
        payroll_run.status = 'paid'
        payroll_run.paid_at = paid_at
        payroll_run.save(update_fields=['status', 'paid_at', 'updated_at'])
        log_action(request, 'update', 'PayrollRun', payroll_run.id, str(payroll_run), 'Payroll run paid.')
        return Response(PayrollRunSerializer(payroll_run).data)


class SalaryViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = SalarySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'slip'):
            return [IsAuthenticated(), RequiresMFAForPayroll()]
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsPayrollManager(), RequiresMFAForPayroll()]
        return [IsPayrollUser(), RequiresMFAForPayroll()]

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

    def perform_create(self, serializer):
        month = serializer.validated_data['month']
        year = serializer.validated_data['year']
        payroll_run, _ = PayrollRun.objects.get_or_create(
            month=month,
            year=year,
            defaults={'created_by': self.request.user},
        )
        if payroll_run.status != 'draft':
            raise serializers.ValidationError(
                {'payroll_run': 'The payroll run for this period is already locked.'},
            )
        serializer.save(payroll_run=payroll_run)

    def update(self, request, *args, **kwargs):
        salary = self.get_object()
        if salary.status != 'draft':
            return Response(
                {'detail': 'Approved or paid payroll records are locked.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        salary = self.get_object()
        if salary.status != 'draft':
            return Response(
                {'detail': 'Approved or paid payroll records cannot be deleted.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

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

    @action(detail=False, methods=['get'], url_path='export')
    def export_logs(self, request):
        from api.compliance_views import audit_log_export_response
        return audit_log_export_response(request)


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
        from documents.access_control import filter_documents_for_user
        from documents.models import HRDocument

        qs = HRDocument.objects.filter(is_active=True).select_related('employee', 'uploaded_by')
        qs = filter_documents_for_user(qs, self.request.user)
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
        from documents.access_control import user_can_upload_document_category
        from api.uploads import validate_upload

        category = serializer.validated_data.get('category', 'other')
        if not user_can_upload_document_category(self.request.user, category):
            raise serializers.ValidationError({'category': 'You cannot upload documents in this category.'})
        upload = serializer.validated_data.get('file')
        if upload:
            validate_upload(upload, kind='document')
        org_id = getattr(self.request.user, 'organization_id', None)
        employee = serializer.save(uploaded_by=self.request.user)
        return employee

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        from documents.models import DocumentAcknowledgement

        document = self.get_object()
        if not document.requires_acknowledgement:
            return Response({'detail': 'This document does not require acknowledgement.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee = Employee.objects.get(email=request.user.email)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee profile linked to your account.'}, status=status.HTTP_400_BAD_REQUEST)

        acknowledgement, created = DocumentAcknowledgement.objects.get_or_create(
            document=document,
            employee=employee,
            defaults={'ip_address': request.META.get('REMOTE_ADDR')},
        )
        from .serializers_phase2 import HRDocumentSerializer
        return Response({
            'acknowledged': True,
            'created': created,
            'document': HRDocumentSerializer(document, context={'request': request}).data,
        })


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

    def get_permissions(self):
        return [IsAdminOrManager()]

    def get_queryset(self):
        from workflows.models import ApprovalRequest
        from workflows.services import get_pending_for_user

        status = self.request.query_params.get('status', 'pending')
        scope = self.request.query_params.get('scope', 'mine')

        if scope == 'all' and self.request.user.is_admin:
            qs = ApprovalRequest.objects.select_related(
                'workflow', 'content_type', 'submitted_by',
            ).prefetch_related('decisions')
        else:
            qs = get_pending_for_user(self.request.user)

        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-submitted_at')

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        from .approval_integration import process_approval_request_decision
        from .serializers_phase2 import ApprovalRequestSerializer

        approval_request = self.get_object()
        outcome = process_approval_request_decision(
            request, approval_request, True, request.data.get('comment', ''),
        )
        if outcome.get('status') == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if outcome.get('status') == 404:
            return Response({'detail': outcome['detail']}, status=status.HTTP_404_NOT_FOUND)
        if outcome.get('status') == 400:
            return Response({'detail': outcome['detail']}, status=status.HTTP_400_BAD_REQUEST)

        approval_request.refresh_from_db()
        return Response({
            'result': outcome.get('result'),
            'approval_request': ApprovalRequestSerializer(approval_request, context={'request': request}).data,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        from .approval_integration import process_approval_request_decision
        from .serializers_phase2 import ApprovalRequestSerializer

        approval_request = self.get_object()
        comment = request.data.get('comment', request.data.get('reason', ''))
        outcome = process_approval_request_decision(
            request, approval_request, False, comment,
        )
        if outcome.get('status') == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if outcome.get('status') == 404:
            return Response({'detail': outcome['detail']}, status=status.HTTP_404_NOT_FOUND)
        if outcome.get('status') == 400:
            return Response({'detail': outcome['detail']}, status=status.HTTP_400_BAD_REQUEST)

        approval_request.refresh_from_db()
        return Response({
            'result': outcome.get('result'),
            'approval_request': ApprovalRequestSerializer(approval_request, context={'request': request}).data,
        })


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_serializer_class(self):
        from .serializers import RoleSerializer
        return RoleSerializer

    def get_permissions(self):
        from django.conf import settings
        from rest_framework.permissions import AllowAny

        if self.action == 'list' and getattr(settings, 'ALLOW_PUBLIC_REGISTRATION', False):
            return [AllowAny()]
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [IsAdmin()]

    def partial_update(self, request, *args, **kwargs):
        role = self.get_object()
        if role.name == Role.ADMIN:
            return Response({'detail': 'Admin role permissions cannot be changed.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(request, 'update', 'Role', role.id, role.name, 'Role permissions updated')
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = CustomUser.objects.select_related('role').order_by('username')
        if self.request.user.is_admin and self.request.query_params.get('include_inactive') == '1':
            return qs
        return qs.filter(is_active=True)

    def get_permissions(self):
        if self.action in ('create', 'partial_update', 'update'):
            return [IsAdmin()]
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [IsAdmin()]

    def get_serializer_class(self):
        from .serializers import AdminUserCreateSerializer, AdminUserUpdateSerializer, UserSerializer
        if self.action == 'create':
            return AdminUserCreateSerializer
        if self.action in ('partial_update', 'update'):
            return AdminUserUpdateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        from .serializers import UserSerializer

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_action(request, 'create', 'CustomUser', user.id, user.username, 'User created by admin')
        return Response(
            UserSerializer(user, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        from .serializers import UserSerializer

        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        if 'is_active' in serializer.validated_data and not updated.is_active:
            Employee.objects.filter(email=updated.email).update(is_active=False)
            log_action(request, 'update', 'CustomUser', updated.id, updated.username, 'User deactivated')
        else:
            log_action(request, 'update', 'CustomUser', updated.id, updated.username, 'User updated by admin')
        return Response(UserSerializer(updated, context=self.get_serializer_context()).data)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


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
        instance, raw_key = APIKey.generate(
            request.user,
            serializer.validated_data['name'],
            scopes=serializer.validated_data.get('scopes') or ['read'],
        )
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

    @action(detail=False, methods=['get'], url_path='delivery-log')
    def delivery_log(self, request):
        from integrations.models import WebhookDelivery
        qs = WebhookDelivery.objects.select_related('endpoint').order_by('-delivered_at')
        endpoint_id = request.query_params.get('endpoint')
        if endpoint_id:
            qs = qs.filter(endpoint_id=endpoint_id)
        success = request.query_params.get('success')
        if success in ('1', 'true'):
            qs = qs.filter(success=True)
        elif success in ('0', 'false'):
            qs = qs.filter(success=False)
        limit = min(int(request.query_params.get('limit', 100)), 200)
        from .integrations_serializers import WebhookDeliverySerializer
        return Response(WebhookDeliverySerializer(qs[:limit], many=True).data)

    @action(detail=False, methods=['post'], url_path='retry-delivery')
    def retry_delivery(self, request):
        from integrations.services import retry_webhook_delivery
        from .integrations_serializers import WebhookDeliverySerializer

        delivery_id = request.data.get('delivery_id')
        if not delivery_id:
            return Response({'detail': 'delivery_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            delivery = retry_webhook_delivery(delivery_id)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(WebhookDeliverySerializer(delivery).data)

    @action(detail=False, methods=['get'])
    def events(self, request):
        from integrations.models import WEBHOOK_EVENTS
        return Response({'events': WEBHOOK_EVENTS})


class SavedReportViewSet(AuditedModelViewSet):
    serializer_class = SavedReportSerializer

    def get_queryset(self):
        from reports.models import SavedReport

        user = self.request.user
        return SavedReport.objects.filter(
            Q(created_by=user) | Q(is_public=True),
        ).select_related('created_by').order_by('-updated_at')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [CanManageReports()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Return saved filters for the SPA to load into the Reports page."""
        saved = self.get_object()
        return Response({
            'report_type': saved.report_type,
            'filters': saved.filters,
            'name': saved.name,
        })


class ReportSnapshotViewSet(AuditedModelViewSet):
    serializer_class = ReportSnapshotSerializer

    def get_queryset(self):
        from reports.models import ReportSnapshot

        qs = ReportSnapshot.objects.select_related('generated_by').order_by('-generated_at')
        report_type = self.request.query_params.get('report_type')
        if report_type:
            qs = qs.filter(report_type=report_type)
        if not self.request.user.is_admin:
            qs = qs.filter(generated_by=self.request.user)
        return qs

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [CanManageReports()]

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)


class ScheduledReportViewSet(AuditedModelViewSet):
    serializer_class = ScheduledReportSerializer

    def get_queryset(self):
        from reports.models import ScheduledReport

        return ScheduledReport.objects.select_related('created_by').order_by('name')

    def get_permissions(self):
        return [CanManageReports()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        from reports.services import deliver_scheduled_report

        scheduled = self.get_object()
        try:
            result = deliver_scheduled_report(scheduled.id)
            return Response(result)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SensitiveDataAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        from .serializers import SensitiveDataAccessLogSerializer
        return SensitiveDataAccessLogSerializer

    def get_queryset(self):
        from accounts.models import SensitiveDataAccessLog

        return SensitiveDataAccessLog.objects.select_related('user', 'employee').order_by('-accessed_at')


class DocumentAccessRuleViewSet(AuditedModelViewSet):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        from .serializers import DocumentAccessRuleSerializer
        return DocumentAccessRuleSerializer

    def get_queryset(self):
        from documents.models import DocumentAccessRule

        return DocumentAccessRule.objects.select_related('role').order_by('role__name', 'category')
