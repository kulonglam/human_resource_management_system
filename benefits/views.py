from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Benefit, EmployeeBenefit
from .forms import BenefitForm, EmployeeBenefitForm, EmployeeBenefitTerminationForm

@login_required
def benefit_list(request):
    benefits = Benefit.objects.filter(is_active=True)
    return render(request, 'benefits/list.html', {'benefits': benefits})

@login_required
def benefit_detail(request, pk):
    benefit = get_object_or_404(Benefit, pk=pk)
    enrollments = benefit.enrollments.filter(status__in=['active', 'pending'])
    return render(request, 'benefits/detail.html', {'benefit': benefit, 'enrollments': enrollments})

@login_required
def benefit_create(request):
    if request.method == 'POST':
        form = BenefitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Benefit created successfully')
            return redirect('benefit_list')
    else:
        form = BenefitForm()
    return render(request, 'benefits/form.html', {'form': form, 'title': 'Create Benefit'})

@login_required
def benefit_update(request, pk):
    benefit = get_object_or_404(Benefit, pk=pk)
    if request.method == 'POST':
        form = BenefitForm(request.POST, instance=benefit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Benefit updated successfully')
            return redirect('benefit_detail', pk=benefit.pk)
    else:
        form = BenefitForm(instance=benefit)
    return render(request, 'benefits/form.html', {'form': form, 'benefit': benefit, 'title': 'Update Benefit'})

@login_required
def enrollment_list(request):
    enrollments = EmployeeBenefit.objects.filter(status__in=['active', 'pending'])
    return render(request, 'benefits/enrollments.html', {'enrollments': enrollments})

@login_required
def enrollment_create(request):
    if request.method == 'POST':
        form = EmployeeBenefitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee benefit enrolled successfully')
            return redirect('enrollment_list')
    else:
        form = EmployeeBenefitForm()
    return render(request, 'benefits/enrollment_form.html', {'form': form, 'title': 'Enroll in Benefit'})

@login_required
def enrollment_terminate(request, pk):
    enrollment = get_object_or_404(EmployeeBenefit, pk=pk)
    if request.method == 'POST':
        form = EmployeeBenefitTerminationForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Benefit enrollment terminated')
            return redirect('enrollment_list')
    else:
        form = EmployeeBenefitTerminationForm(instance=enrollment)
    return render(request, 'benefits/terminate.html', {'form': form, 'enrollment': enrollment})
