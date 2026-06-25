from datetime import datetime, timedelta

from django.db.models import Avg, Count, F, Sum, Value
from django.db.models.functions import Concat
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.models import Attendance
from departments.models import Department
from leaves.models import Leave, LeaveBalance
from payroll.models import Salary
from performance.models import PerformanceAppraisal, PerformanceGoal
from recruitment.models import Application, JobPosting

from .report_exports import export_key_value_xlsx, export_rows_csv, export_rows_xlsx


def _maybe_export(request, payload, columns, filename_prefix):
    export_format = request.query_params.get('format', '').lower()
    if export_format not in ('csv', 'xlsx'):
        return None
    rows = payload.get('rows') or payload.get('records') or []
    if not rows and payload.get('funnel'):
        rows = [{'status': k, 'count': v} for k, v in payload['funnel'].items()]
        columns = [{'key': 'status', 'label': 'Stage'}, {'key': 'count', 'label': 'Count'}]
    if export_format == 'csv':
        return export_rows_csv(rows, columns, filename_prefix)
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
        records = list(
            query.annotate(
                employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
            ).values('employee_name', 'date', 'status', 'time_in', 'time_out')[:500]
        )

        payload = {
            'period': f'{start_date} to {end_date}',
            'total_records': query.count(),
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
                gross_salary=F('basic_salary') + F('allowances'),
            ).values('employee_name', 'basic_salary', 'allowances', 'deductions', 'tax', 'net_salary', 'gross_salary')
        )

        payload = {
            'period': f'{month}/{year}',
            'total_employees': query.count(),
            'total_gross': query.aggregate(v=Sum(F('basic_salary') + F('allowances')))['v'] or 0,
            'total_net': query.aggregate(v=Sum('net_salary'))['v'] or 0,
            'total_tax': query.aggregate(v=Sum('tax'))['v'] or 0,
            'rows': salaries,
        }
        exported = _maybe_export(request, payload, [
            {'key': 'employee_name', 'label': 'Employee'},
            {'key': 'basic_salary', 'label': 'Basic'},
            {'key': 'allowances', 'label': 'Allowances'},
            {'key': 'deductions', 'label': 'Deductions'},
            {'key': 'tax', 'label': 'Tax'},
            {'key': 'net_salary', 'label': 'Net'},
            {'key': 'gross_salary', 'label': 'Gross'},
        ], 'payroll_report')
        if exported:
            return exported
        return Response(payload)


class PerformanceReportView(APIView):
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
        export_format = request.query_params.get('format', '').lower()
        if export_format == 'xlsx':
            return export_key_value_xlsx({
                'Total jobs': payload['total_jobs'],
                'Open positions': payload['open_positions'],
                'Closed positions': payload['closed_positions'],
            }, 'job_summary_report', 'Job Summary')
        return Response(payload)


class ReportFiltersView(APIView):
    """Metadata for report filter dropdowns."""

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
        })
