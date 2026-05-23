# accounts/views.py
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect

from .forms import LoginForm, UserRegistrationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': request.GET.get('next', '')})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    from employees.models import Employee
    from departments.models import Department
    from leaves.models import Leave, LeaveBalance
    from recruitment.models import JobPosting
    from performance.models import PerformanceGoal, PerformanceAppraisal
    from training.models import TrainingCourse, TrainingRecord, DevelopmentPlan, EmployeeCertification
    from django.utils import timezone
    from datetime import timedelta

    context = {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'total_departments': Department.objects.count(),
        'pending_leaves': Leave.objects.filter(status='pending').count(),
        'open_jobs': JobPosting.objects.filter(is_open=True).count(),
        'total_goals': PerformanceGoal.objects.count(),
        'active_goals': PerformanceGoal.objects.filter(status='in_progress').count(),
        'total_appraisals': PerformanceAppraisal.objects.count(),
        'active_courses': TrainingCourse.objects.filter(status='active').count(),
        'upcoming_courses': TrainingCourse.objects.filter(status='planned').count(),
        'total_employees_trained': TrainingRecord.objects.filter(status='completed').values('employee').distinct().count(),
        'expiring_certifications': EmployeeCertification.objects.filter(
            expiry_date__lte=timezone.now() + timedelta(days=30),
            expiry_date__gte=timezone.now()
        ).count(),
        'active_development_plans': DevelopmentPlan.objects.filter(status='active').count(),
    }
    
    # Recent trainings (last 5)
    recent_trainings = TrainingRecord.objects.filter(status='completed').order_by('-completion_date')[:5]
    context['recent_trainings'] = recent_trainings
    
    # Certifications expiring soon
    certifications_expiring_soon = EmployeeCertification.objects.filter(
        expiry_date__lte=timezone.now() + timedelta(days=30),
        expiry_date__gte=timezone.now()
    ).order_by('expiry_date')[:5]
    context['certifications_expiring_soon'] = certifications_expiring_soon
    
    current_year = timezone.now().year
    
    # Get user's employee profile
    try:
        employee = Employee.objects.get(email=request.user.email)
        
        # Get user's leave balance
        leave_balances = LeaveBalance.objects.filter(
            employee=employee,
            year=current_year
        ).order_by('leave_type')
        context['user_leave_balances'] = leave_balances
        context['employee'] = employee
        
        # Manager: Get department leave summary
        if request.user.is_manager and employee.department:
            dept_employees = Employee.objects.filter(
                department=employee.department,
                is_active=True
            )
            dept_balances = LeaveBalance.objects.filter(
                employee__in=dept_employees,
                year=current_year
            )
            context['dept_leave_summary'] = {
                'total_used': sum(b.used_days for b in dept_balances),
                'total_pending': sum(b.pending_days for b in dept_balances),
                'total_available': sum(b.available_days for b in dept_balances),
                'employee_count': dept_employees.count(),
            }
        
        # Admin: Get all employees leave summary
        if request.user.is_admin:
            all_balances = LeaveBalance.objects.filter(year=current_year)
            context['all_leave_summary'] = {
                'total_used': sum(b.used_days for b in all_balances),
                'total_pending': sum(b.pending_days for b in all_balances),
                'total_available': sum(b.available_days for b in all_balances),
                'total_allocated': sum(b.total_days for b in all_balances),
            }
    except Employee.DoesNotExist:
        pass
    
    return render(request, 'dashboard.html', context)