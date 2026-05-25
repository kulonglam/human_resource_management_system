from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Shift, ShiftAssignment
from .forms import ShiftForm, ShiftAssignmentForm

@login_required
def shift_list(request):
    shifts = Shift.objects.filter(is_active=True)
    return render(request, 'shifts/list.html', {'shifts': shifts})

@login_required
def shift_detail(request, pk):
    shift = get_object_or_404(Shift, pk=pk)
    assignments = shift.assignments.filter(status='active')
    return render(request, 'shifts/detail.html', {'shift': shift, 'assignments': assignments})

@login_required
def shift_create(request):
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift created successfully')
            return redirect('shift_list')
    else:
        form = ShiftForm()
    return render(request, 'shifts/form.html', {'form': form, 'title': 'Create Shift'})

@login_required
def shift_update(request, pk):
    shift = get_object_or_404(Shift, pk=pk)
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift updated successfully')
            return redirect('shift_detail', pk=shift.pk)
    else:
        form = ShiftForm(instance=shift)
    return render(request, 'shifts/form.html', {'form': form, 'shift': shift, 'title': 'Update Shift'})

@login_required
def shift_assignment_list(request):
    assignments = ShiftAssignment.objects.filter(status__in=['active', 'inactive'])
    return render(request, 'shifts/assignments.html', {'assignments': assignments})

@login_required
def shift_assign(request):
    if request.method == 'POST':
        form = ShiftAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift assigned successfully')
            return redirect('shift_assignment_list')
    else:
        form = ShiftAssignmentForm()
    return render(request, 'shifts/assign.html', {'form': form})

@login_required
def shift_assignment_update(request, pk):
    assignment = get_object_or_404(ShiftAssignment, pk=pk)
    if request.method == 'POST':
        form = ShiftAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift assignment updated')
            return redirect('shift_assignment_list')
    else:
        form = ShiftAssignmentForm(instance=assignment)
    return render(request, 'shifts/assign.html', {'form': form, 'assignment': assignment})
