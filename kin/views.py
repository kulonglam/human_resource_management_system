from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from employees.models import Employee
from .models import Kin
from .forms import KinForm

@login_required
def kin_create_or_edit(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    kin_instance = getattr(employee, 'kin', None)
    form = KinForm(request.POST or None, instance=kin_instance)
    if form.is_valid():
        kin = form.save(commit=False)
        kin.employee = employee
        kin.save()
        return redirect('employee_detail', pk=employee_pk)
    return render(request, 'kin/form.html', {'form': form, 'employee': employee})
