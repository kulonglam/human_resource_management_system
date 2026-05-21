from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from employees.models import Employee
from .models import Attendance
from .forms import AttendanceForm

@login_required
def attendance_list(request):
    today = timezone.now().date()
    records = Attendance.objects.filter(date=today).select_related('employee')
    return render(request, 'attendance/list.html', {'records': records, 'today': today})

@login_required
def mark_attendance(request):
    employees = Employee.objects.filter(is_active=True)
    today = timezone.now().date()
    if request.method == 'POST':
        count = 0
        for emp in employees:
            status = request.POST.get(f'status_{emp.id}')
            if status:
                Attendance.objects.update_or_create(
                    employee=emp, date=today,
                    defaults={
                        'status': status,
                        'time_in': request.POST.get(f'time_in_{emp.id}') or None,
                        'time_out': request.POST.get(f'time_out_{emp.id}') or None,
                    }
                )
                count += 1
        messages.success(request, f"Attendance marked for {count} employee(s).")
        return redirect('attendance_list')
    already_marked = Attendance.objects.filter(date=today).values_list('employee_id', flat=True)
    return render(request, 'attendance/mark.html', {
        'employees': employees,
        'today': today,
        'already_marked': already_marked,
    })

@login_required
def attendance_report(request):
    employee_id = request.GET.get('employee')
    month = request.GET.get('month')
    records = Attendance.objects.all()
    if employee_id:
        records = records.filter(employee_id=employee_id)
    if month:
        records = records.filter(date__month=month)
    employees = Employee.objects.filter(is_active=True)
    return render(request, 'attendance/report.html', {
        'records': records, 'employees': employees
    })