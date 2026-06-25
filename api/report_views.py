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

        return Response({
            'period': f'{start_date} to {end_date}',
            'total_records': query.count(),
            'status_breakdown': {s['status']: s['count'] for s in stats},
            'records': records,
        })


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
            return Response({'type': 'Balance', 'year': year, 'rows': data})

        if report_type == 'pending':
            pending = list(
                query.filter(status='pending').annotate(
                    employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
                ).values('employee_name', 'leave_type', 'start_date', 'end_date', 'applied_on')
            )
            return Response({'type': 'Pending', 'year': year, 'rows': pending, 'total': len(pending)})

        if report_type == 'detailed':
            leaves = list(
                query.annotate(
                    employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
                ).values('employee_name', 'leave_type', 'start_date', 'end_date', 'status', 'reason')
            )
            return Response({'type': 'Detailed', 'year': year, 'rows': leaves})

        summary = list(query.values('leave_type').annotate(count=Count('id')))
        return Response({'type': 'Summary', 'year': year, 'rows': summary})


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

        return Response({
            'period': f'{month}/{year}',
            'total_employees': query.count(),
            'total_gross': query.aggregate(v=Sum(F('basic_salary') + F('allowances')))['v'] or 0,
            'total_net': query.aggregate(v=Sum('net_salary'))['v'] or 0,
            'total_tax': query.aggregate(v=Sum('tax'))['v'] or 0,
            'rows': salaries,
        })


class PerformanceReportView(APIView):
    def get(self, request):
        report_type = request.query_params.get('report_type', 'appraisal_summary')
        department = request.query_params.get('department')

        if report_type == 'goal_progress':
            goals = PerformanceGoal.objects.all()
            if department:
                goals = goals.filter(employee__department_id=department)
            return Response({
                'type': 'Goal Progress',
                'total_goals': goals.count(),
                'average_progress': round(goals.aggregate(v=Avg('progress'))['v'] or 0, 1),
                'rows': list(goals.values('status').annotate(count=Count('id'))),
            })

        query = PerformanceAppraisal.objects.all()
        if department:
            query = query.filter(employee__department_id=department)

        rating = request.query_params.get('rating')
        if rating:
            query = query.filter(overall_rating=rating)

        return Response({
            'type': 'Appraisal Summary',
            'total_appraisals': query.count(),
            'average_rating': round(query.aggregate(v=Avg('overall_rating'))['v'] or 0, 2),
            'rows': list(query.values('overall_rating').annotate(count=Count('id'))),
        })


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
            return Response({
                'type': 'Applicant Status',
                'total_applications': apps.count(),
                'rows': list(apps.values('status').annotate(count=Count('id'))),
            })

        if report_type == 'hiring_funnel':
            apps = Application.objects.filter(job__in=jobs)
            funnel = {s: apps.filter(status=s).count() for s in [
                'received', 'shortlisted', 'interviewed', 'hired', 'rejected'
            ]}
            return Response({'type': 'Hiring Funnel', 'funnel': funnel})

        return Response({
            'type': 'Job Summary',
            'total_jobs': jobs.count(),
            'open_positions': jobs.filter(is_open=True).count(),
            'closed_positions': jobs.filter(is_open=False).count(),
        })


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
