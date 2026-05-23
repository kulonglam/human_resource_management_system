from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Q
from .models import (
    PerformanceGoal, PerformanceAppraisal, FeedbackRound, 
    FeedbackRequest, Feedback, FeedbackSummary
)
from .forms import (
    PerformanceGoalForm, PerformanceAppraisalForm, 
    FeedbackRoundForm, FeedbackForm
)
from employees.models import Employee


# ==================== PERFORMANCE GOALS ====================

@login_required
def goal_list(request):
    """List all performance goals."""
    goals = PerformanceGoal.objects.all().select_related('employee', 'set_by')
    
    # Filtering
    status = request.GET.get('status')
    employee = request.GET.get('employee')
    
    if status:
        goals = goals.filter(status=status)
    if employee:
        goals = goals.filter(employee__id=employee)
    
    employees = Employee.objects.all()
    return render(request, 'performance/goals/list.html', {
        'goals': goals,
        'employees': employees,
        'selected_status': status,
        'selected_employee': employee,
    })


@login_required
def goal_create(request):
    """Create a new performance goal."""
    form = PerformanceGoalForm(request.POST or None)
    if form.is_valid():
        goal = form.save(commit=False)
        goal.set_by = request.user
        goal.save()
        messages.success(request, f"Performance goal '{goal.goal_title}' created successfully.")
        return redirect('goal_list')
    return render(request, 'performance/goals/form.html', {
        'form': form,
        'title': 'Add Performance Goal'
    })


@login_required
def goal_detail(request, pk):
    """View goal details."""
    goal = get_object_or_404(PerformanceGoal, pk=pk)
    return render(request, 'performance/goals/detail.html', {'goal': goal})


@login_required
def goal_edit(request, pk):
    """Edit a performance goal."""
    goal = get_object_or_404(PerformanceGoal, pk=pk)
    form = PerformanceGoalForm(request.POST or None, instance=goal)
    if form.is_valid():
        form.save()
        messages.success(request, f"Performance goal updated successfully.")
        return redirect('goal_detail', pk=goal.pk)
    return render(request, 'performance/goals/form.html', {
        'form': form,
        'title': 'Edit Performance Goal',
        'goal': goal
    })


@login_required
def goal_delete(request, pk):
    """Delete a performance goal."""
    goal = get_object_or_404(PerformanceGoal, pk=pk)
    if request.method == 'POST':
        goal_title = goal.goal_title
        goal.delete()
        messages.success(request, f"Performance goal '{goal_title}' deleted successfully.")
        return redirect('goal_list')
    return render(request, 'performance/goals/confirm_delete.html', {'goal': goal})


# ==================== PERFORMANCE APPRAISALS ====================

@login_required
def appraisal_list(request):
    """List all performance appraisals."""
    appraisals = PerformanceAppraisal.objects.all().select_related('employee', 'appraiser')
    
    # Filtering
    status = request.GET.get('status')
    employee = request.GET.get('employee')
    
    if status:
        appraisals = appraisals.filter(status=status)
    if employee:
        appraisals = appraisals.filter(employee__id=employee)
    
    employees = Employee.objects.all()
    return render(request, 'performance/appraisals/list.html', {
        'appraisals': appraisals,
        'employees': employees,
        'selected_status': status,
        'selected_employee': employee,
    })


@login_required
def appraisal_create(request):
    """Create a new appraisal."""
    form = PerformanceAppraisalForm(request.POST or None)
    if form.is_valid():
        appraisal = form.save()
        messages.success(request, f"Performance appraisal created for {appraisal.employee.full_name}.")
        return redirect('appraisal_list')
    return render(request, 'performance/appraisals/form.html', {
        'form': form,
        'title': 'Create Performance Appraisal'
    })


@login_required
def appraisal_detail(request, pk):
    """View appraisal details."""
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk)
    return render(request, 'performance/appraisals/detail.html', {'appraisal': appraisal})


@login_required
def appraisal_edit(request, pk):
    """Edit an appraisal."""
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk)
    form = PerformanceAppraisalForm(request.POST or None, instance=appraisal)
    if form.is_valid():
        appraisal = form.save(commit=False)
        if request.POST.get('action') == 'submit':
            appraisal.status = 'submitted'
            appraisal.submitted_at = timezone.now()
        form.save()
        messages.success(request, "Appraisal updated successfully.")
        return redirect('appraisal_detail', pk=appraisal.pk)
    return render(request, 'performance/appraisals/form.html', {
        'form': form,
        'title': 'Edit Performance Appraisal',
        'appraisal': appraisal
    })


@login_required
def appraisal_submit(request, pk):
    """Submit an appraisal for review."""
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk)
    if request.method == 'POST':
        appraisal.status = 'submitted'
        appraisal.submitted_at = timezone.now()
        appraisal.save()
        messages.success(request, "Appraisal submitted for review.")
    return redirect('appraisal_detail', pk=pk)


@login_required
def appraisal_approve(request, pk):
    """Approve an appraisal."""
    appraisal = get_object_or_404(PerformanceAppraisal, pk=pk)
    if request.method == 'POST':
        appraisal.status = 'approved'
        appraisal.approved_at = timezone.now()
        appraisal.save()
        messages.success(request, "Appraisal approved successfully.")
    return redirect('appraisal_detail', pk=pk)


# ==================== 360 FEEDBACK ====================

@login_required
def feedback_round_list(request):
    """List all feedback rounds."""
    rounds = FeedbackRound.objects.all().select_related('created_by').order_by('-created_at')
    return render(request, 'performance/feedback/rounds_list.html', {'rounds': rounds})


@login_required
def feedback_round_create(request):
    """Create a new feedback round."""
    form = FeedbackRoundForm(request.POST or None)
    if form.is_valid():
        round_obj = form.save(commit=False)
        round_obj.created_by = request.user
        round_obj.save()
        messages.success(request, f"Feedback round '{round_obj.name}' created successfully.")
        return redirect('feedback_round_detail', pk=round_obj.pk)
    return render(request, 'performance/feedback/round_form.html', {
        'form': form,
        'title': 'Create Feedback Round'
    })


@login_required
def feedback_round_detail(request, pk):
    """View feedback round details."""
    round_obj = get_object_or_404(FeedbackRound, pk=pk)
    feedback_requests = round_obj.feedback_requests.select_related('recipient', 'feedback_giver')
    
    # Statistics
    total_requests = feedback_requests.count()
    submitted = feedback_requests.filter(status='submitted').count()
    pending = feedback_requests.filter(status='pending').count()
    
    return render(request, 'performance/feedback/round_detail.html', {
        'round': round_obj,
        'feedback_requests': feedback_requests,
        'total_requests': total_requests,
        'submitted': submitted,
        'pending': pending,
    })


@login_required
def feedback_request_create(request, round_id):
    """Create feedback requests for employees in a round."""
    round_obj = get_object_or_404(FeedbackRound, pk=round_id)
    
    if request.method == 'POST':
        # Bulk create feedback requests
        employee_ids = request.POST.getlist('employees')
        giver_users = request.POST.getlist('givers')
        giver_types = request.POST.getlist('giver_types')
        
        created_count = 0
        for employee_id in employee_ids:
            employee = get_object_or_404(Employee, pk=employee_id)
            for giver_id, giver_type in zip(giver_users, giver_types):
                giver = get_object_or_404(CustomUser, pk=giver_id)
                try:
                    FeedbackRequest.objects.create(
                        feedback_round=round_obj,
                        recipient=employee,
                        feedback_giver=giver,
                        giver_type=giver_type
                    )
                    created_count += 1
                except:
                    pass  # Skip duplicates
        
        messages.success(request, f"{created_count} feedback requests created.")
        return redirect('feedback_round_detail', pk=round_id)
    
    employees = Employee.objects.all()
    users = CustomUser.objects.all()
    giver_types = [('manager', 'Manager'), ('peer', 'Peer'), ('direct_report', 'Direct Report')]
    
    return render(request, 'performance/feedback/request_create.html', {
        'round': round_obj,
        'employees': employees,
        'users': users,
        'giver_types': giver_types,
    })


@login_required
def feedback_submit(request, request_id):
    """Submit feedback for a feedback request."""
    feedback_request = get_object_or_404(FeedbackRequest, pk=request_id)
    
    # Check if already submitted
    if feedback_request.status == 'submitted':
        messages.info(request, "Feedback already submitted for this request.")
        return redirect('my_feedback_requests')
    
    # Check if current user is the feedback giver
    if request.user != feedback_request.feedback_giver:
        messages.error(request, "You are not authorized to submit feedback for this request.")
        return redirect('my_feedback_requests')
    
    # Get or create feedback instance
    try:
        feedback = feedback_request.feedback
        form = FeedbackForm(request.POST or None, instance=feedback)
    except Feedback.DoesNotExist:
        form = FeedbackForm(request.POST or None)
    
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.request = feedback_request
        feedback.save()
        feedback_request.status = 'submitted'
        feedback_request.submitted_at = timezone.now()
        feedback_request.save()
        messages.success(request, "Feedback submitted successfully.")
        return redirect('my_feedback_requests')
    
    return render(request, 'performance/feedback/submit.html', {
        'form': form,
        'feedback_request': feedback_request,
        'recipient': feedback_request.recipient,
    })


@login_required
def my_feedback_requests(request):
    """View feedback requests assigned to current user."""
    requests = FeedbackRequest.objects.filter(feedback_giver=request.user).select_related(
        'feedback_round', 'recipient'
    ).order_by('-created_at')
    
    pending = requests.filter(status='pending').count()
    submitted = requests.filter(status='submitted').count()
    
    return render(request, 'performance/feedback/my_requests.html', {
        'requests': requests,
        'pending': pending,
        'submitted': submitted,
    })


@login_required
def feedback_summary_view(request, employee_id):
    """View 360-degree feedback summary for an employee."""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    try:
        summary = employee.feedback_summary
    except FeedbackSummary.DoesNotExist:
        summary = None
    
    # Get all feedback for this employee
    feedback_requests = FeedbackRequest.objects.filter(
        recipient=employee,
        status='submitted'
    ).select_related('feedback_round', 'feedback_giver')
    
    return render(request, 'performance/feedback/summary.html', {
        'employee': employee,
        'summary': summary,
        'feedback_requests': feedback_requests,
    })


@login_required
def dashboard(request):
    """Performance management dashboard."""
    # Overall statistics
    total_goals = PerformanceGoal.objects.count()
    active_goals = PerformanceGoal.objects.filter(status='in_progress').count()
    total_appraisals = PerformanceAppraisal.objects.count()
    active_feedback_rounds = FeedbackRound.objects.filter(status='active').count()
    pending_feedback = FeedbackRequest.objects.filter(status='pending').count()
    
    # Recent appraisals
    recent_appraisals = PerformanceAppraisal.objects.all().select_related('employee').order_by('-created_at')[:5]
    
    # Upcoming feedback rounds
    upcoming_rounds = FeedbackRound.objects.filter(end_date__gte=timezone.now().date()).order_by('end_date')[:5]
    
    context = {
        'total_goals': total_goals,
        'active_goals': active_goals,
        'total_appraisals': total_appraisals,
        'active_feedback_rounds': active_feedback_rounds,
        'pending_feedback': pending_feedback,
        'recent_appraisals': recent_appraisals,
        'upcoming_rounds': upcoming_rounds,
    }
    
    return render(request, 'performance/dashboard.html', context)
