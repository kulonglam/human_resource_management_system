from datetime import datetime, timedelta

from django.db.models import Avg, Count, F, Sum, Value
from django.db.models.functions import Concat
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.models import Attendance
from departments.models import Department
from employees.models import Employee
from leaves.models import Leave, LeaveBalance
from payroll.models import Salary
from performance.models import PerformanceAppraisal, PerformanceGoal
from recruitment.models import Application, JobPosting

from .permissions import IsAdminOrManager
from .report_exports import export_key_value_xlsx, export_rows_csv, export_rows_pdf, export_rows_xlsx


def build_reports_overview():
    """Workforce snapshot cards for the Reports overview tab."""
    today = timezone.now().date()
    return {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'new_joiners': Employee.objects.filter(
            date_joined__gte=today - timedelta(days=30), is_active=True
        ).count(),
        'present_today': Attendance.objects.filter(date=today, status='present').count(),
        'absent_today': Attendance.objects.filter(date=today, status='absent').count(),
        'late_today': Attendance.objects.filter(date=today, status='late').count(),
        'pending_leaves': Leave.objects.filter(status='pending').count(),
        'leaves_used_this_year': Leave.objects.filter(
            status='approved', start_date__year=today.year
        ).count(),
        'open_positions': JobPosting.objects.filter(is_open=True).count(),
        'pending_applications': Application.objects.filter(status='received').count(),
        'active_goals': PerformanceGoal.objects.filter(status='in_progress').count(),
        'appraisals_due': PerformanceAppraisal.objects.filter(
            status__in=['draft', 'submitted'],
            appraisal_period_end__lte=today,
        ).count(),
    }


def _maybe_export(request, payload, columns, filename_prefix):
    export_format = request.query_params.get(
        'export_format', request.query_params.get('format', '')
    ).lower()
    if export_format not in ('csv', 'xlsx', 'pdf'):
        return None
    rows = payload.get('rows') or payload.get('records') or []
    if not rows and payload.get('funnel'):
        rows = [{'status': k, 'count': v} for k, v in payload['funnel'].items()]
        columns = [{'key': 'status', 'label': 'Stage'}, {'key': 'count', 'label': 'Count'}]
    if export_format == 'csv':
        return export_rows_csv(rows, columns, filename_prefix)
    if export_format == 'pdf':
        return export_rows_pdf(rows, columns, filename_prefix, filename_prefix.replace('_', ' ').title())
    return export_rows_xlsx(rows, columns, filename_prefix)


def _parse_date(value):
    if hasattr(value, 'year'):
        return value
    return datetime.strptime(str(value), '%Y-%m-%d').date()


def _date_range(params):
    date_range = params.get('date_range', 'this_month')
    today = timezone.now().date()
    if date_range == 'last_month':
        first = today.replace(day=1)
        last = first - timedelta(days=1)
        return last.replace(day=1), last
    if date_range == 'this_quarter':
        q_start = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=q_start, day=1), today
    if date_range == 'this_year':
        return today.replace(month=1, day=1), today
    if date_range == 'custom':
        start = params.get('start_date')
        end = params.get('end_date')
        if start and end:
            return _parse_date(start), _parse_date(end)
    return today.replace(day=1), today


class AttendanceReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        start_date, end_date = _date_range(request.query_params)
        query = Attendance.objects.filter(date__range=[start_date, end_date])

        department = request.query_params.get('department')
        if department:
            query = query.filter(employee__department_id=department)

        status = request.query_params.get('status')
        if status:
            query = query.filter(status=status)

        stats = query.values('status').annotate(count=Count('id'))
        records_query = query.annotate(
            employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
        ).values('employee_name', 'date', 'status', 'time_in', 'time_out')
        total_records = query.count()
        export_requested = request.query_params.get(
            'export_format', request.query_params.get('format', '')
        ).lower() in ('csv', 'xlsx')
        records = list(records_query if export_requested else records_query[:500])
        payload = {
            'period': f'{start_date} to {end_date}',
            'total_records': total_records,
            'shown_records': len(records),
            'truncated': not export_requested and total_records > len(records),
            'status_breakdown': {s['status']: s['count'] for s in stats},
            'records': records,
        }
        exported = _maybe_export(
            request, payload,
            [
                {'key': 'employee_name', 'label': 'Employee'},
                {'key': 'date', 'label': 'Date'},
                {'key': 'status', 'label': 'Status'},
                {'key': 'time_in', 'label': 'Time In'},
                {'key': 'time_out', 'label': 'Time Out'},
            ],
            'attendance_report',
        )
        if exported:
            return exported
        return Response(payload)


class LeaveReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        report_type = request.query_params.get('report_type', 'summary')
        year = int(request.query_params.get('year', timezone.now().year))
        query = Leave.objects.filter(start_date__year=year)

        department = request.query_params.get('department')
        if department:
            query = query.filter(employee__department_id=department)

        leave_type = request.query_params.get('leave_type')
        if leave_type:
            query = query.filter(leave_type=leave_type)

        status = request.query_params.get('status')
        if status:
            query = query.filter(status=status)

        if report_type == 'balance':
            balances = LeaveBalance.objects.filter(year=year)
            if department:
                balances = balances.filter(employee__department_id=department)
            data = list(
                balances.annotate(
                    employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
                ).values('employee_name', 'leave_type', 'total_days', 'used_days', 'pending_days')
            )
            payload = {'type': 'Balance', 'year': year, 'rows': data}
            exported = _maybe_export(request, payload, [
                {'key': 'employee_name', 'label': 'Employee'},
                {'key': 'leave_type', 'label': 'Type'},
                {'key': 'total_days', 'label': 'Total'},
                {'key': 'used_days', 'label': 'Used'},
                {'key': 'pending_days', 'label': 'Pending'},
            ], 'leave_balance_report')
            if exported:
                return exported
            return Response(payload)

        if report_type == 'pending':
            pending = list(
                query.filter(status='pending').annotate(
                    employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
                ).values('employee_name', 'leave_type', 'start_date', 'end_date', 'applied_on')
            )
            payload = {'type': 'Pending', 'year': year, 'rows': pending, 'total': len(pending)}
            exported = _maybe_export(request, payload, [
                {'key': 'employee_name', 'label': 'Employee'},
                {'key': 'leave_type', 'label': 'Type'},
                {'key': 'start_date', 'label': 'Start'},
                {'key': 'end_date', 'label': 'End'},
                {'key': 'applied_on', 'label': 'Applied On'},
            ], 'leave_pending_report')
            if exported:
                return exported
            return Response(payload)

        if report_type == 'detailed':
            leaves = list(
                query.annotate(
                    employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
                ).values('employee_name', 'leave_type', 'start_date', 'end_date', 'status', 'reason')
            )
            payload = {'type': 'Detailed', 'year': year, 'rows': leaves}
            exported = _maybe_export(request, payload, [
                {'key': 'employee_name', 'label': 'Employee'},
                {'key': 'leave_type', 'label': 'Type'},
                {'key': 'start_date', 'label': 'Start'},
                {'key': 'end_date', 'label': 'End'},
                {'key': 'status', 'label': 'Status'},
                {'key': 'reason', 'label': 'Reason'},
            ], 'leave_detailed_report')
            if exported:
                return exported
            return Response(payload)

        summary = list(query.values('leave_type').annotate(count=Count('id')))
        payload = {'type': 'Summary', 'year': year, 'rows': summary}
        exported = _maybe_export(request, payload, [
            {'key': 'leave_type', 'label': 'Leave Type'},
            {'key': 'count', 'label': 'Count'},
        ], 'leave_summary_report')
        if exported:
            return exported
        return Response(payload)


class PayrollReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        query = Salary.objects.filter(month=month, year=year)

        department = request.query_params.get('department')
        if department:
            query = query.filter(employee__department_id=department)

        salaries = list(
            query.annotate(
                employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name')),
            ).values(
                'employee_name', 'basic_salary', 'allowances', 'taxable_benefits',
                'gross_salary', 'chargeable_income', 'tax', 'nssf_employee',
                'nssf_employer', 'local_service_tax', 'deductions', 'net_salary', 'status',
            )
        )

        payload = {
            'period': f'{month}/{year}',
            'total_employees': query.count(),
            'total_gross': query.aggregate(v=Sum('gross_salary'))['v'] or 0,
            'total_net': query.aggregate(v=Sum('net_salary'))['v'] or 0,
            'total_tax': query.aggregate(v=Sum('tax'))['v'] or 0,
            'total_nssf_employee': query.aggregate(v=Sum('nssf_employee'))['v'] or 0,
            'total_nssf_employer': query.aggregate(v=Sum('nssf_employer'))['v'] or 0,
            'total_local_service_tax': query.aggregate(v=Sum('local_service_tax'))['v'] or 0,
            'rows': salaries,
        }
        exported = _maybe_export(request, payload, [
            {'key': 'employee_name', 'label': 'Employee'},
            {'key': 'basic_salary', 'label': 'Basic'},
            {'key': 'allowances', 'label': 'Allowances'},
            {'key': 'taxable_benefits', 'label': 'Taxable Benefits'},
            {'key': 'gross_salary', 'label': 'Gross'},
            {'key': 'chargeable_income', 'label': 'PAYE Chargeable Income'},
            {'key': 'tax', 'label': 'PAYE'},
            {'key': 'nssf_employee', 'label': 'Employee NSSF (5%)'},
            {'key': 'nssf_employer', 'label': 'Employer NSSF (10%)'},
            {'key': 'local_service_tax', 'label': 'Local Service Tax'},
            {'key': 'deductions', 'label': 'Deductions'},
            {'key': 'net_salary', 'label': 'Net'},
            {'key': 'status', 'label': 'Status'},
        ], 'payroll_report')
        if exported:
            return exported
        return Response(payload)


class PerformanceReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        report_type = request.query_params.get('report_type', 'appraisal_summary')
        department = request.query_params.get('department')

        if report_type == 'goal_progress':
            goals = PerformanceGoal.objects.all()
            if department:
                goals = goals.filter(employee__department_id=department)
            payload = {
                'type': 'Goal Progress',
                'total_goals': goals.count(),
                'average_progress': round(goals.aggregate(v=Avg('progress'))['v'] or 0, 1),
                'rows': list(goals.values('status').annotate(count=Count('id'))),
            }
            exported = _maybe_export(request, payload, [
                {'key': 'status', 'label': 'Status'},
                {'key': 'count', 'label': 'Count'},
            ], 'goal_progress_report')
            if exported:
                return exported
            return Response(payload)

        query = PerformanceAppraisal.objects.all()
        if department:
            query = query.filter(employee__department_id=department)

        rating = request.query_params.get('rating')
        if rating:
            query = query.filter(overall_rating=rating)

        payload = {
            'type': 'Appraisal Summary',
            'total_appraisals': query.count(),
            'average_rating': round(query.aggregate(v=Avg('overall_rating'))['v'] or 0, 2),
            'rows': list(query.values('overall_rating').annotate(count=Count('id'))),
        }
        exported = _maybe_export(request, payload, [
            {'key': 'overall_rating', 'label': 'Rating'},
            {'key': 'count', 'label': 'Count'},
        ], 'appraisal_summary_report')
        if exported:
            return exported
        return Response(payload)


class RecruitmentReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        report_type = request.query_params.get('report_type', 'job_summary')
        department = request.query_params.get('department')

        jobs = JobPosting.objects.all()
        if department:
            jobs = jobs.filter(department=department)

        job_status = request.query_params.get('job_status')
        if job_status == 'open':
            jobs = jobs.filter(is_open=True)
        elif job_status == 'closed':
            jobs = jobs.filter(is_open=False)

        if report_type == 'applicant_status':
            apps = Application.objects.filter(job__in=jobs)
            payload = {
                'type': 'Applicant Status',
                'total_applications': apps.count(),
                'rows': list(apps.values('status').annotate(count=Count('id'))),
            }
            exported = _maybe_export(request, payload, [
                {'key': 'status', 'label': 'Status'},
                {'key': 'count', 'label': 'Count'},
            ], 'applicant_status_report')
            if exported:
                return exported
            return Response(payload)

        if report_type == 'hiring_funnel':
            apps = Application.objects.filter(job__in=jobs)
            funnel = {s: apps.filter(status=s).count() for s in [
                'received', 'shortlisted', 'interviewed', 'hired', 'rejected'
            ]}
            payload = {'type': 'Hiring Funnel', 'funnel': funnel}
            exported = _maybe_export(request, payload, [], 'hiring_funnel_report')
            if exported:
                return exported
            return Response(payload)

        payload = {
            'type': 'Job Summary',
            'total_jobs': jobs.count(),
            'open_positions': jobs.filter(is_open=True).count(),
            'closed_positions': jobs.filter(is_open=False).count(),
        }
        export_format = request.query_params.get(
            'export_format', request.query_params.get('format', '')
        ).lower()
        if export_format == 'xlsx':
            return export_key_value_xlsx({
                'Total jobs': payload['total_jobs'],
                'Open positions': payload['open_positions'],
                'Closed positions': payload['closed_positions'],
            }, 'job_summary_report', 'Job Summary')
        return Response(payload)


class ReportFiltersView(APIView):
    """Report filter dropdowns plus overview metrics (successor to /reports/analytics/)."""

    permission_classes = [IsAdminOrManager]

    def get(self, request):
        return Response({
            'departments': list(Department.objects.values('id', 'name')),
            'years': list(range(timezone.now().year, timezone.now().year - 5, -1)),
            'months': [
                {'value': i, 'label': name}
                for i, name in enumerate(
                    ['January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November', 'December'],
                    start=1,
                )
            ],
            'overview': build_reports_overview(),
        })
