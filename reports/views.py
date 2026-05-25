from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, Avg, F
from django.db.models.functions import Concat
from django.db.models import Value
from django.utils import timezone
from datetime import timedelta, datetime
import json

from employees.models import Employee
from departments.models import Department
from attendance.models import Attendance
from leaves.models import Leave, LeaveBalance
from payroll.models import Salary
from recruitment.models import JobPosting, Application
from performance.models import PerformanceAppraisal, PerformanceGoal

from .forms import (
    AttendanceReportForm, LeaveReportForm, PayrollReportForm,
    PerformanceReportForm, RecruitmentReportForm, HRAnalyticsForm
)
from .models import SavedReport, ReportSnapshot


@login_required
def analytics_dashboard(request):
    """Main HR Analytics Dashboard with key metrics."""
    context = {}
    
    # Employee statistics
    total_employees = Employee.objects.filter(is_active=True).count()
    new_joiners = Employee.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30),
        is_active=True
    ).count()
    
    # Attendance metrics
    today = timezone.now().date()
    present_today = Attendance.objects.filter(
        date=today,
        status='present'
    ).count()
    absent_today = Attendance.objects.filter(
        date=today,
        status='absent'
    ).count()
    late_today = Attendance.objects.filter(
        date=today,
        status='late'
    ).count()
    
    # Leave metrics
    pending_leaves = Leave.objects.filter(status='pending').count()
    leaves_used_this_year = Leave.objects.filter(
        status='approved',
        start_date__year=timezone.now().year
    ).count()
    
    # Recruitment metrics
    open_positions = JobPosting.objects.filter(is_open=True).count()
    pending_applications = Application.objects.filter(status='received').count()
    
    # Performance metrics
    active_goals = PerformanceGoal.objects.filter(status='in_progress').count()
    appraisals_due = PerformanceAppraisal.objects.filter(
        status__in=['draft', 'submitted'],
        appraisal_period_end__lte=timezone.now().date()
    ).count()
    
    context.update({
        'total_employees': total_employees,
        'new_joiners': new_joiners,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'pending_leaves': pending_leaves,
        'leaves_used_this_year': leaves_used_this_year,
        'open_positions': open_positions,
        'pending_applications': pending_applications,
        'active_goals': active_goals,
        'appraisals_due': appraisals_due,
    })
    
    return render(request, 'reports/analytics_dashboard.html', context)


@login_required
def attendance_report(request):
    """Generate attendance reports with filtering."""
    form = AttendanceReportForm(request.GET or None)
    report_data = None
    
    if form.is_valid():
        # Determine date range
        date_range = form.cleaned_data['date_range']
        today = timezone.now().date()
        
        if date_range == 'this_month':
            start_date = today.replace(day=1)
            end_date = today
        elif date_range == 'last_month':
            first_day_current = today.replace(day=1)
            last_day_previous = first_day_current - timedelta(days=1)
            start_date = last_day_previous.replace(day=1)
            end_date = last_day_previous
        elif date_range == 'this_quarter':
            quarter_start = ((today.month - 1) // 3) * 3 + 1
            start_date = today.replace(month=quarter_start, day=1)
            end_date = today
        elif date_range == 'this_year':
            start_date = today.replace(month=1, day=1)
            end_date = today
        else:  # custom
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
        
        # Build query
        query = Attendance.objects.filter(
            date__range=[start_date, end_date]
        )
        
        # Filter by department
        department = form.cleaned_data.get('department')
        if department:
            query = query.filter(employee__department=department)
        
        # Filter by attendance status
        statuses = form.cleaned_data.get('attendance_status')
        if statuses:
            query = query.filter(status__in=statuses)
        
        # Group statistics
        attendance_stats = query.values('status').annotate(count=Count('id'))
        status_breakdown = {stat['status']: stat['count'] for stat in attendance_stats}
        
        total_records = query.count()
        
        report_data = {
            'period': f"{start_date} to {end_date}",
            'total_records': total_records,
            'status_breakdown': status_breakdown,
            'department': str(department) if department else 'All Departments',
            'records': list(query.annotate(
                employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
            ).values('employee_name', 'date', 'status', 'time_in', 'time_out'))
        }
    
    context = {
        'form': form,
        'report_data': report_data,
        'report_type': 'Attendance Report'
    }
    return render(request, 'reports/attendance_report.html', context)


@login_required
def leave_report(request):
    """Generate leave reports with filtering."""
    form = LeaveReportForm(request.GET or None)
    report_data = None
    
    if form.is_valid():
        report_type = form.cleaned_data['report_type']
        year = form.cleaned_data['year']
        
        # Build base query
        query = Leave.objects.filter(start_date__year=year)
        
        # Apply filters
        department = form.cleaned_data.get('department')
        if department:
            query = query.filter(employee__department=department)
        
        leave_types = form.cleaned_data.get('leave_type')
        if leave_types:
            query = query.filter(leave_type__in=leave_types)
        
        statuses = form.cleaned_data.get('status')
        if statuses:
            query = query.filter(status__in=statuses)
        
        if report_type == 'summary':
            # Leave summary by type
            summary = query.values('leave_type').annotate(
                count=Count('id')
            )
            report_data = {
                'type': 'Summary',
                'year': year,
                'summary': list(summary)
            }
        elif report_type == 'balance':
            # Leave balance report
            balances = LeaveBalance.objects.filter(year=year)
            if department:
                balances = balances.filter(employee__department=department)
            
            balance_data = list(balances.annotate(
                employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
            ).values(
                'leave_type',
                'employee_name',
                'total_days',
                'used_days',
                'pending_days'
            ).annotate(
                available=F('total_days') - F('used_days') - F('pending_days')
            ))
            report_data = {
                'type': 'Balance',
                'year': year,
                'balances': balance_data
            }
        elif report_type == 'detailed':
            # Detailed leave records
            leaves = list(query.annotate(
                employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
            ).values(
                'employee_name',
                'leave_type',
                'start_date',
                'end_date',
                'status',
                'reason'
            ))
            report_data = {
                'type': 'Detailed',
                'year': year,
                'leaves': leaves,
                'total_records': len(leaves)
            }
        elif report_type == 'pending':
            # Pending approvals
            pending = list(query.filter(status='pending').annotate(
                employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name')),
                duration=F('end_date') - F('start_date')
            ).values(
                'employee_name',
                'leave_type',
                'start_date',
                'end_date',
                'applied_on',
                'duration'
            ))
            report_data = {
                'type': 'Pending Approvals',
                'year': year,
                'pending_leaves': pending,
                'total_pending': len(pending)
            }
    
    context = {
        'form': form,
        'report_data': report_data,
        'report_type': 'Leave Report'
    }
    return render(request, 'reports/leave_report.html', context)


@login_required
def payroll_report(request):
    """Generate payroll reports with filtering."""
    form = PayrollReportForm(request.GET or None)
    report_data = None
    
    if form.is_valid():
        month = form.cleaned_data['month']
        year = form.cleaned_data['year']
        
        # Build base query
        query = Salary.objects.filter(
            month=month,
            year=year
        )
        
        department = form.cleaned_data.get('department')
        if department:
            query = query.filter(employee__department=department)
        
        employee_status = form.cleaned_data.get('employee_status', [])
        if 'active' in employee_status:
            query = query.filter(employee__is_active=True)
        if 'inactive' in employee_status:
            query = query.filter(employee__is_active=False)
        
        # Calculate gross salary (basic + allowances)
        salaries_with_gross = query.annotate(
            gross_salary=F('basic_salary') + F('allowances'),
            employee_name=Concat(F('employee__first_name'), Value(' '), F('employee__last_name'))
        )
        
        # Payroll summary
        total_gross = salaries_with_gross.aggregate(Sum('gross_salary'))['gross_salary__sum'] or 0
        total_net = query.aggregate(Sum('net_salary'))['net_salary__sum'] or 0
        total_deductions = query.aggregate(Sum('deductions'))['deductions__sum'] or 0
        total_tax = query.aggregate(Sum('tax'))['tax__sum'] or 0
        
        salary_records = list(salaries_with_gross.values(
            'employee_name',
            'employee__id',
            'basic_salary',
            'allowances',
            'deductions',
            'tax',
            'net_salary'
        ).annotate(gross_salary=F('basic_salary') + F('allowances')))
        
        report_data = {
            'period': f"{month}/{year}",
            'total_employees': query.count(),
            'total_gross': total_gross,
            'total_allowances': query.aggregate(Sum('allowances'))['allowances__sum'] or 0,
            'total_deductions': total_deductions,
            'total_tax': total_tax,
            'total_net': total_net,
            'salaries': salary_records
        }
    
    context = {
        'form': form,
        'report_data': report_data,
        'report_type': 'Payroll Report'
    }
    return render(request, 'reports/payroll_report.html', context)


@login_required
def performance_report(request):
    """Generate performance reports."""
    form = PerformanceReportForm(request.GET or None)
    report_data = None
    
    if form.is_valid():
        report_type = form.cleaned_data['report_type']
        appraisal_period = form.cleaned_data['appraisal_period']
        
        query = PerformanceAppraisal.objects.all()
        
        department = form.cleaned_data.get('department')
        if department:
            query = query.filter(employee__department=department)
        
        ratings = form.cleaned_data.get('performance_rating')
        if ratings:
            query = query.filter(overall_rating__in=ratings)
        
        if report_type == 'appraisal_summary':
            # Summary of appraisals
            summary = query.values('overall_rating').annotate(count=Count('id'))
            avg_rating = query.aggregate(Avg('overall_rating'))['overall_rating__avg'] or 0
            
            report_data = {
                'type': 'Appraisal Summary',
                'total_appraisals': query.count(),
                'average_rating': round(avg_rating, 2),
                'rating_distribution': list(summary)
            }
        elif report_type == 'goal_progress':
            # Goal progress
            goals = PerformanceGoal.objects.all()
            if department:
                goals = goals.filter(employee__department=department)
            
            progress_summary = goals.values('status').annotate(count=Count('id'))
            avg_progress = goals.aggregate(Avg('progress'))['progress__avg'] or 0
            
            report_data = {
                'type': 'Goal Progress',
                'total_goals': goals.count(),
                'average_progress': round(avg_progress, 1),
                'status_distribution': list(progress_summary)
            }
    
    context = {
        'form': form,
        'report_data': report_data,
        'report_type': 'Performance Report'
    }
    return render(request, 'reports/performance_report.html', context)


@login_required
def recruitment_report(request):
    """Generate recruitment reports."""
    form = RecruitmentReportForm(request.GET or None)
    report_data = None
    
    if form.is_valid():
        report_type = form.cleaned_data['report_type']
        
        job_query = JobPosting.objects.all()
        department = form.cleaned_data.get('department')
        if department:
            job_query = job_query.filter(department=department)
        
        job_statuses = form.cleaned_data.get('job_status')
        if job_statuses:
            if 'open' in job_statuses:
                job_query = job_query.filter(is_open=True)
            elif 'closed' in job_statuses:
                job_query = job_query.filter(is_open=False)
        
        if report_type == 'job_summary':
            report_data = {
                'type': 'Job Summary',
                'total_jobs': job_query.count(),
                'open_positions': job_query.filter(is_open=True).count(),
                'closed_positions': job_query.filter(is_open=False).count(),
            }
        elif report_type == 'applicant_status':
            app_query = Application.objects.filter(job__in=job_query)
            app_summary = app_query.values('status').annotate(count=Count('id'))
            
            report_data = {
                'type': 'Applicant Status',
                'total_applications': app_query.count(),
                'status_breakdown': list(app_summary)
            }
        elif report_type == 'hiring_funnel':
            app_query = Application.objects.filter(job__in=job_query)
            # Use actual status values from Application model
            statuses = ['received', 'shortlisted', 'interviewed', 'hired', 'rejected']
            funnel_data = {}
            for status in statuses:
                funnel_data[status] = app_query.filter(status=status).count()
            
            report_data = {
                'type': 'Hiring Funnel',
                'funnel': funnel_data
            }
    
    context = {
        'form': form,
        'report_data': report_data,
        'report_type': 'Recruitment Report'
    }
    return render(request, 'reports/recruitment_report.html', context)
