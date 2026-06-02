from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import Leave, LeaveBalance
from .forms import LeaveForm
from employees.models import Employee
from accounts.access_control import get_user_accessible_employees
from datetime import datetime

@login_required
def leave_list(request):
    leaves = Leave.objects.all().select_related('employee')
    
    # Get leave balances for all employees or current user's balances
    current_year = timezone.now().year
    balances = LeaveBalance.objects.filter(year=current_year).select_related('employee')
    
    return render(request, 'leaves/list.html', {
        'leaves': leaves,
        'balances': balances,
        'current_year': current_year
    })

@login_required
def leave_apply(request):
    form = LeaveForm(request.POST or None)
    balances = []
    current_year = timezone.now().year
    selected_employee = None
    
    # Filter form employees based on user access
    accessible_employees = get_user_accessible_employees(request.user)
    form.fields['employee'].queryset = accessible_employees
    
    if form.is_valid():
        leave = form.save(commit=False)
        
        # Check leave balance
        try:
            balance = LeaveBalance.objects.get(
                employee=leave.employee,
                leave_type=leave.leave_type,
                year=current_year
            )
            
            if balance.available_days < leave.duration:
                messages.error(
                    request, 
                    f"Insufficient leave balance. Available: {balance.available_days} days, Requested: {leave.duration} days"
                )
                balances = LeaveBalance.objects.filter(
                    employee=leave.employee,
                    year=current_year
                ).order_by('leave_type')
                return render(request, 'leaves/form.html', {'form': form, 'balances': balances, 'current_year': current_year})
            
            # Add pending days
            balance.pending_days += leave.duration
            balance.save()
        except LeaveBalance.DoesNotExist:
            messages.warning(request, "Leave balance not configured for this employee and leave type.")
        
        leave.save()
        messages.success(request, "Leave application submitted successfully.")
        return redirect('leave_list')
    
    # Get balances for selected employee if any
    # Check if employee_id is in the request (GET parameter or form data)
    employee_id = request.GET.get('employee_id') or request.POST.get('employee')
    
    if employee_id:
        try:
            selected_employee = accessible_employees.get(pk=employee_id)
            balances = LeaveBalance.objects.filter(
                employee=selected_employee,
                year=current_year
            ).order_by('leave_type')
        except Employee.DoesNotExist:
            pass
    
    return render(request, 'leaves/form.html', {
        'form': form,
        'balances': balances,
        'current_year': current_year,
        'selected_employee': selected_employee
    })

@login_required
def leave_approve(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            # Update leave balance
            current_year = timezone.now().year
            try:
                balance = LeaveBalance.objects.get(
                    employee=leave.employee,
                    leave_type=leave.leave_type,
                    year=current_year
                )
                # Move from pending to used
                balance.pending_days -= leave.duration
                balance.used_days += leave.duration
                balance.save()
            except LeaveBalance.DoesNotExist:
                pass
            
            leave.status = 'approved'
        else:
            # Reject - return pending days
            current_year = timezone.now().year
            try:
                balance = LeaveBalance.objects.get(
                    employee=leave.employee,
                    leave_type=leave.leave_type,
                    year=current_year
                )
                balance.pending_days -= leave.duration
                balance.save()
            except LeaveBalance.DoesNotExist:
                pass
            
            leave.status = 'rejected'
        
        leave.reviewed_by = request.user.get_full_name() or request.user.username
        leave.reviewed_on = timezone.now()
        leave.save()
        messages.success(request, f"Leave request {leave.status}.")
        return redirect('leave_list')
    return render(request, 'leaves/approve.html', {'leave': leave})

@login_required
def leave_reject(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == 'POST':
        leave.status = 'rejected'
        leave.reviewed_by = request.user.get_full_name() or request.user.username
        leave.reviewed_on = timezone.now()
        leave.save()
        messages.success(request, "Leave request rejected.")
        return redirect('leave_list')
    return render(request, 'leaves/reject.html', {'leave': leave})