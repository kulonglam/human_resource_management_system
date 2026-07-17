import json
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone

from accounts.models import AuditLog, CustomUser
from assets.models import AssetAssignment
from attendance.models import Attendance
from benefits.models import EmployeeBenefit
from discipline.models import Discipline, DisciplineAppeal
from employees.models import Employee
from exits.models import ExitProcess
from expenses.models import Expense
from kin.models import Kin
from leaves.models import Leave, LeaveBalance
from payroll.models import Salary
from performance.models import PerformanceAppraisal, PerformanceGoal
from shifts.models import ShiftAssignment
from surveys.models import SurveyResponse
from training.models import (
    DevelopmentPlan,
    EmployeeCertification,
    EmployeeSkill,
    TrainingRecord,
)

from api.serializers import (
    ApplicationSerializer,
    AttendanceSerializer,
    EmployeeSerializer,
    ExpenseSerializer,
    KinSerializer,
    LeaveBalanceSerializer,
    LeaveSerializer,
    PublicApplicationSerializer,
    PublicJobPostingSerializer,
    SalarySerializer,
    UserSerializer,
)


def _serialize_many(serializer_class, queryset, request):
    return serializer_class(queryset, many=True, context={'request': request}).data


def _serialize_one(serializer_class, instance, request):
    return serializer_class(instance, context={'request': request}).data


def build_employee_data_export(employee, request=None):
    """Collect personal data held about an employee for GDPR subject access requests."""
    linked_user = CustomUser.objects.filter(email=employee.email).first()
    audit_logs = AuditLog.objects.filter(
        model_name__in=['Employee', 'Leave', 'Expense', 'CustomUser'],
        object_id__in=[employee.pk] + list(
            Leave.objects.filter(employee=employee).values_list('pk', flat=True)
        ),
    ).order_by('-timestamp')[:500]

    user_account = None
    if linked_user:
        user_account = UserSerializer(linked_user).data

    return {
        'export_type': 'gdpr_subject_access',
        'exported_at': timezone.now().isoformat(),
        'employee_id': employee.pk,
        'subject_name': employee.full_name,
        'profile': _serialize_one(EmployeeSerializer, employee, request),
        'user_account': user_account,
        'next_of_kin': _serialize_many(KinSerializer, Kin.objects.filter(employee=employee), request),
        'leave_requests': _serialize_many(LeaveSerializer, Leave.objects.filter(employee=employee), request),
        'leave_balances': _serialize_many(
            LeaveBalanceSerializer, LeaveBalance.objects.filter(employee=employee), request,
        ),
        'attendance': _serialize_many(
            AttendanceSerializer, Attendance.objects.filter(employee=employee), request,
        ),
        'payroll': _serialize_many(SalarySerializer, Salary.objects.filter(employee=employee), request),
        'expenses': _serialize_many(ExpenseSerializer, Expense.objects.filter(employee=employee), request),
        'benefits': [
            {
                'benefit': eb.benefit.name,
                'enrollment_date': eb.enrollment_date.isoformat() if eb.enrollment_date else None,
                'status': eb.status,
            }
            for eb in EmployeeBenefit.objects.filter(employee=employee).select_related('benefit')
        ],
        'performance_goals': [
            {
                'title': g.goal_title,
                'status': g.status,
                'end_date': g.end_date.isoformat() if g.end_date else None,
                'progress': g.progress,
            }
            for g in PerformanceGoal.objects.filter(employee=employee)
        ],
        'performance_appraisals': [
            {
                'period_start': a.appraisal_period_start.isoformat() if a.appraisal_period_start else None,
                'period_end': a.appraisal_period_end.isoformat() if a.appraisal_period_end else None,
                'overall_rating': a.overall_rating,
                'status': a.status,
            }
            for a in PerformanceAppraisal.objects.filter(employee=employee)
        ],
        'training_records': [
            {
                'course': tr.course.title if tr.course else None,
                'status': tr.status,
                'completion_date': tr.completion_date.isoformat() if tr.completion_date else None,
            }
            for tr in TrainingRecord.objects.filter(employee=employee).select_related('course')
        ],
        'certifications': [
            {
                'certification': ec.certification.name if ec.certification else None,
                'issue_date': ec.issue_date.isoformat() if ec.issue_date else None,
                'expiry_date': ec.expiry_date.isoformat() if ec.expiry_date else None,
            }
            for ec in EmployeeCertification.objects.filter(employee=employee).select_related('certification')
        ],
        'skills': [
            {'skill': es.skill.name, 'proficiency': es.proficiency_level}
            for es in EmployeeSkill.objects.filter(employee=employee).select_related('skill')
        ],
        'development_plans': [
            {
                'title': dp.title,
                'status': dp.status,
                'end_date': dp.end_date.isoformat() if dp.end_date else None,
            }
            for dp in DevelopmentPlan.objects.filter(employee=employee)
        ],
        'discipline_records': [
            {
                'incident_date': d.incident_date.isoformat() if d.incident_date else None,
                'discipline_type': d.discipline_type,
                'status': d.status,
            }
            for d in Discipline.objects.filter(employee=employee)
        ],
        'discipline_appeals': [
            {'status': a.status, 'appeal_date': a.appeal_date.isoformat() if a.appeal_date else None}
            for a in DisciplineAppeal.objects.filter(discipline__employee=employee)
        ],
        'asset_assignments': [
            {
                'asset': aa.asset.name if aa.asset else None,
                'assigned_date': aa.assignment_date.isoformat() if aa.assignment_date else None,
                'returned_date': aa.return_date.isoformat() if aa.return_date else None,
            }
            for aa in AssetAssignment.objects.filter(employee=employee).select_related('asset')
        ],
        'shift_assignments': [
            {
                'shift': sa.shift.shift_name if sa.shift else None,
                'start_date': sa.start_date.isoformat() if sa.start_date else None,
                'end_date': sa.end_date.isoformat() if sa.end_date else None,
            }
            for sa in ShiftAssignment.objects.filter(employee=employee).select_related('shift')
        ],
        'exit_processes': [
            {'status': ep.status, 'last_working_day': ep.last_working_day.isoformat() if ep.last_working_day else None}
            for ep in ExitProcess.objects.filter(employee=employee)
        ],
        'survey_responses': [
            {
                'survey': sr.survey.title if sr.survey else None,
                'submitted_at': sr.created_at.isoformat() if sr.created_at else None,
            }
            for sr in SurveyResponse.objects.filter(respondent=employee).select_related('survey')
        ],
        'audit_trail': [
            {
                'timestamp': log.timestamp.isoformat(),
                'action': log.action,
                'model_name': log.model_name,
                'details': log.details,
            }
            for log in audit_logs
        ],
    }


def export_json_response(payload, filename_prefix='gdpr_export'):
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    content = json.dumps(payload, indent=2, default=str)
    response = HttpResponse(content, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{stamp}.json"'
    return response


def anonymize_employee(employee):
    """Anonymize personal data while retaining aggregate employment history where required."""
    old_email = employee.email
    employee.first_name = 'Redacted'
    employee.last_name = f'Employee-{employee.pk}'
    employee.email = f'redacted-{employee.pk}@anon.local'
    employee.mobile = '0000000000'
    employee.address = 'Redacted'
    employee.emergency_contact = '0000000000'
    employee.account_number = '0000000000'
    employee.bank = 'Redacted'
    employee.exit_notes = ''
    if employee.photo:
        employee.photo.delete(save=False)
        employee.photo = None
    employee.is_active = False
    employee.save()

    user = CustomUser.objects.filter(email=old_email).first()
    if user:
        user.is_active = False
        user.email = f'redacted-user-{user.pk}@anon.local'
        user.first_name = 'Redacted'
        user.last_name = f'User-{user.pk}'
        user.save(update_fields=['is_active', 'email', 'first_name', 'last_name'])

    return employee
