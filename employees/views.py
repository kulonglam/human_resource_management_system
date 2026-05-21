from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Employee
from .forms import EmployeeForm
from accounts.access_control import get_user_accessible_employees, can_access_employee

@login_required
def employee_list(request):
    query = request.GET.get('q', '')
    # Get employees accessible by user
    employees = get_user_accessible_employees(request.user).filter(is_active=True)
    
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(job_title__icontains=query) |
            Q(department__name__icontains=query)
        )
    return render(request, 'employees/list.html', {'employees': employees, 'query': query})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    # Check access
    if not can_access_employee(request.user, employee):
        messages.error(request, "You do not have permission to view this employee's details.")
        return redirect('employee_list')
    
    return render(request, 'employees/detail.html', {'employee': employee})

@login_required
def employee_create(request):
    # Only admins can create employees
    if not (hasattr(request.user, 'is_admin') and request.user.is_admin):
        messages.error(request, "You do not have permission to add employees.")
        return redirect('employee_list')
    
    form = EmployeeForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Employee added successfully.")
        return redirect('employee_list')
    return render(request, 'employees/form.html', {'form': form, 'title': 'Add Employee'})

@login_required
def employee_edit(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    
    # Check access
    if not can_access_employee(request.user, emp):
        messages.error(request, "You do not have permission to edit this employee.")
        return redirect('employee_list')
    
    form = EmployeeForm(request.POST or None, request.FILES or None, instance=emp)
    if form.is_valid():
        form.save()
        messages.success(request, "Employee updated successfully.")
        return redirect('employee_detail', pk=pk)
    return render(request, 'employees/form.html', {'form': form, 'title': 'Edit Employee'})


@login_required
def employee_terminate(request, pk):
    """Terminate an employee."""
    emp = get_object_or_404(Employee, pk=pk)
    
    # Only admins can terminate
    if not (hasattr(request.user, 'is_admin') and request.user.is_admin):
        messages.error(request, "You do not have permission to terminate employees.")
        return redirect('employee_detail', pk=pk)
    
    if request.method == 'POST':
        emp.is_active = False
        emp.termination_date = timezone.now().date()
        emp.exit_reason = request.POST.get('exit_reason')
        emp.exit_notes = request.POST.get('exit_notes')
        emp.save()
        
        # Deactivate associated user account
        if hasattr(emp, 'user'):
            emp.user.is_active = False
            emp.user.save()
        
        messages.success(request, f"Employee {emp.full_name} has been terminated.")
        return redirect('employee_list')
    
    return render(request, 'employees/terminate.html', {
        'employee': emp,
        'exit_reasons': Employee.EXIT_REASON_CHOICES
    })