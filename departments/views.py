from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Department
from .forms import DepartmentForm

@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'departments/list.html', {'departments': departments})

@login_required
def department_create(request):
    form = DepartmentForm(request.POST or None)
    if form.is_valid():
        dept = form.save()
        messages.success(request, f"Department '{dept.name}' created successfully.")
        return redirect('department_list')
    return render(request, 'departments/form.html', {'form': form, 'title': 'Add Department'})

@login_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if form.is_valid():
        form.save()
        messages.success(request, f"Department '{dept.name}' updated successfully.")
        return redirect('department_list')
    return render(request, 'departments/form.html', {'form': form, 'title': 'Edit Department'})

@login_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept_name = dept.name
        dept.delete()
        messages.success(request, f"Department '{dept_name}' deleted successfully.")
        return redirect('department_list')
    return render(request, 'departments/confirm_delete.html', {'obj': dept})