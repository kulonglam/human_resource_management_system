from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LeavePolicy, LeavePolicyAllocation
from .forms import LeavePolicyForm, LeavePolicyAllocationForm
from django.utils import timezone

@login_required
def policy_list(request):
    policies = LeavePolicy.objects.filter(is_active=True)
    return render(request, 'leave_policies/list.html', {'policies': policies})

@login_required
def policy_detail(request, pk):
    policy = get_object_or_404(LeavePolicy, pk=pk)
    allocations = policy.allocations.all()
    return render(request, 'leave_policies/detail.html', {'policy': policy, 'allocations': allocations})

@login_required
def policy_create(request):
    if request.method == 'POST':
        form = LeavePolicyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave policy created successfully')
            return redirect('policy_list')
    else:
        form = LeavePolicyForm()
    return render(request, 'leave_policies/form.html', {'form': form, 'title': 'Create Leave Policy'})

@login_required
def policy_update(request, pk):
    policy = get_object_or_404(LeavePolicy, pk=pk)
    if request.method == 'POST':
        form = LeavePolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave policy updated successfully')
            return redirect('policy_detail', pk=policy.pk)
    else:
        form = LeavePolicyForm(instance=policy)
    return render(request, 'leave_policies/form.html', {'form': form, 'policy': policy, 'title': 'Update Leave Policy'})

@login_required
def allocation_list(request):
    current_year = timezone.now().year
    allocations = LeavePolicyAllocation.objects.filter(allocation_year=current_year)
    return render(request, 'leave_policies/allocations.html', {'allocations': allocations})

@login_required
def allocation_create(request):
    if request.method == 'POST':
        form = LeavePolicyAllocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave allocation created successfully')
            return redirect('allocation_list')
    else:
        form = LeavePolicyAllocationForm()
    return render(request, 'leave_policies/allocation_form.html', {'form': form, 'title': 'Create Leave Allocation'})
