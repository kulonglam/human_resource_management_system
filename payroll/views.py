# payroll/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Salary
from .forms import SalaryForm
from .utils import generate_salary_slip_pdf

MONTHS = [
    (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
    (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
    (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
]


@login_required
def salary_list(request):
    salaries = Salary.objects.all().select_related('employee').order_by('-year', '-month')

    month = request.GET.get('month')
    year = request.GET.get('year')
    if month:
        salaries = salaries.filter(month=month)
    if year:
        salaries = salaries.filter(year=year)

    return render(request, 'payroll/list.html', {
        'salaries': salaries,
        'months': MONTHS,
    })


@login_required
def salary_create(request):
    form = SalaryForm(request.POST or None)
    if form.is_valid():
        salary = form.save()
        messages.success(request, f"Salary record created for {salary.employee.full_name} successfully.")
        return redirect('salary_list')
    return render(request, 'payroll/form.html', {'form': form, 'title': 'Add Salary Record'})


@login_required
def salary_edit(request, pk):
    salary = get_object_or_404(Salary, pk=pk)
    form = SalaryForm(request.POST or None, instance=salary)
    if form.is_valid():
        form.save()
        messages.success(request, f"Salary record for {salary.employee.full_name} updated successfully.")
        return redirect('salary_list')
    return render(request, 'payroll/form.html', {'form': form, 'title': 'Edit Salary Record'})


@login_required
def salary_slip_pdf(request, pk):
    """Generate and download salary slip as PDF."""
    salary = get_object_or_404(Salary, pk=pk)
    return generate_salary_slip_pdf(salary)

