from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from datetime import date, timedelta
from .models import (
    Skill, EmployeeSkill, TrainingCourse, TrainingRecord,
    Certification, EmployeeCertification, DevelopmentPlan
)
from .forms import (
    SkillForm, EmployeeSkillForm, TrainingCourseForm, TrainingRecordForm,
    CertificationForm, EmployeeCertificationForm, DevelopmentPlanForm
)
from employees.models import Employee


# ==================== SKILLS ====================

@login_required
def skill_list(request):
    """List all skills."""
    skills = Skill.objects.all().annotate(employee_count=Count('employees'))
    category = request.GET.get('category')
    
    if category:
        skills = skills.filter(category=category)
    
    return render(request, 'training/skills/list.html', {
        'skills': skills,
        'selected_category': category,
    })


@login_required
def skill_create(request):
    """Create a new skill."""
    form = SkillForm(request.POST or None)
    if form.is_valid():
        skill = form.save()
        messages.success(request, f"Skill '{skill.name}' created successfully.")
        return redirect('skill_list')
    return render(request, 'training/skills/form.html', {
        'form': form,
        'title': 'Add Skill'
    })


@login_required
def employee_skill_list(request):
    """List employee skills."""
    employee_skills = EmployeeSkill.objects.all().select_related('employee', 'skill')
    employee = request.GET.get('employee')
    verified = request.GET.get('verified')
    
    if employee:
        employee_skills = employee_skills.filter(employee__id=employee)
    if verified:
        employee_skills = employee_skills.filter(verified=verified == 'true')
    
    employees = Employee.objects.all()
    return render(request, 'training/skills/employee_skills_list.html', {
        'employee_skills': employee_skills,
        'employees': employees,
        'selected_employee': employee,
        'selected_verified': verified,
    })


@login_required
def employee_skill_create(request):
    """Add skill to employee."""
    form = EmployeeSkillForm(request.POST or None)
    if form.is_valid():
        emp_skill = form.save()
        messages.success(request, f"Skill added to {emp_skill.employee.full_name}.")
        return redirect('employee_skill_list')
    return render(request, 'training/skills/employee_skill_form.html', {
        'form': form,
        'title': 'Add Skill to Employee'
    })


@login_required
def employee_skill_edit(request, pk):
    """Edit employee skill."""
    emp_skill = get_object_or_404(EmployeeSkill, pk=pk)
    form = EmployeeSkillForm(request.POST or None, instance=emp_skill)
    if form.is_valid():
        form.save()
        messages.success(request, "Skill updated successfully.")
        return redirect('employee_skill_list')
    return render(request, 'training/skills/employee_skill_form.html', {
        'form': form,
        'title': 'Edit Employee Skill',
        'emp_skill': emp_skill
    })


@login_required
def employee_skill_delete(request, pk):
    """Delete employee skill."""
    emp_skill = get_object_or_404(EmployeeSkill, pk=pk)
    if request.method == 'POST':
        emp_skill.delete()
        messages.success(request, "Skill removed successfully.")
        return redirect('employee_skill_list')
    return render(request, 'training/skills/confirm_delete.html', {'skill': emp_skill})


# ==================== TRAINING COURSES ====================

@login_required
def course_list(request):
    """List all training courses."""
    courses = TrainingCourse.objects.all().annotate(participants=Count('trainings'))
    status = request.GET.get('status')
    category = request.GET.get('category')
    
    if status:
        courses = courses.filter(status=status)
    if category:
        courses = courses.filter(category=category)
    
    return render(request, 'training/courses/list.html', {
        'courses': courses,
        'selected_status': status,
        'selected_category': category,
    })


@login_required
def course_create(request):
    """Create a new training course."""
    form = TrainingCourseForm(request.POST or None)
    if form.is_valid():
        course = form.save(commit=False)
        course.created_by = request.user
        course.save()
        form.save_m2m()
        messages.success(request, f"Course '{course.title}' created successfully.")
        return redirect('course_list')
    return render(request, 'training/courses/form.html', {
        'form': form,
        'title': 'Create Training Course'
    })


@login_required
def course_detail(request, pk):
    """View course details."""
    course = get_object_or_404(TrainingCourse, pk=pk)
    trainings = course.trainings.all().select_related('employee')
    return render(request, 'training/courses/detail.html', {
        'course': course,
        'trainings': trainings,
    })


@login_required
def course_edit(request, pk):
    """Edit a training course."""
    course = get_object_or_404(TrainingCourse, pk=pk)
    form = TrainingCourseForm(request.POST or None, instance=course)
    if form.is_valid():
        form.save()
        messages.success(request, "Course updated successfully.")
        return redirect('course_detail', pk=course.pk)
    return render(request, 'training/courses/form.html', {
        'form': form,
        'title': 'Edit Training Course',
        'course': course
    })


# ==================== TRAINING RECORDS ====================

@login_required
def training_record_list(request):
    """List all training records."""
    records = TrainingRecord.objects.all().select_related('employee', 'course')
    status = request.GET.get('status')
    employee = request.GET.get('employee')
    
    if status:
        records = records.filter(status=status)
    if employee:
        records = records.filter(employee__id=employee)
    
    employees = Employee.objects.all()
    return render(request, 'training/training_records/list.html', {
        'records': records,
        'employees': employees,
        'selected_status': status,
        'selected_employee': employee,
    })


@login_required
def training_record_create(request):
    """Enroll employee in training."""
    form = TrainingRecordForm(request.POST or None)
    if form.is_valid():
        record = form.save()
        messages.success(request, f"{record.employee.full_name} enrolled in {record.course.title}.")
        return redirect('training_record_list')
    return render(request, 'training/training_records/form.html', {
        'form': form,
        'title': 'Enroll in Training'
    })


@login_required
def training_record_edit(request, pk):
    """Edit training record."""
    record = get_object_or_404(TrainingRecord, pk=pk)
    form = TrainingRecordForm(request.POST or None, instance=record)
    if form.is_valid():
        form.save()
        messages.success(request, "Training record updated successfully.")
        return redirect('training_record_list')
    return render(request, 'training/training_records/form.html', {
        'form': form,
        'title': 'Edit Training Record',
        'record': record
    })


# ==================== CERTIFICATIONS ====================

@login_required
def certification_list(request):
    """List all certifications."""
    certs = Certification.objects.all().annotate(employee_count=Count('employees'))
    return render(request, 'training/certifications/list.html', {'certifications': certs})


@login_required
def certification_create(request):
    """Create a new certification type."""
    form = CertificationForm(request.POST or None)
    if form.is_valid():
        cert = form.save()
        messages.success(request, f"Certification '{cert.name}' created.")
        return redirect('certification_list')
    return render(request, 'training/certifications/form.html', {
        'form': form,
        'title': 'Add Certification'
    })


@login_required
def employee_certification_list(request):
    """List employee certifications."""
    emp_certs = EmployeeCertification.objects.all().select_related('employee', 'certification')
    employee = request.GET.get('employee')
    status = request.GET.get('status')
    
    if employee:
        emp_certs = emp_certs.filter(employee__id=employee)
    if status:
        emp_certs = emp_certs.filter(status=status)
    
    # Highlight expiring soon
    for cert in emp_certs:
        if cert.is_expiring_soon:
            cert.expiring_soon_flag = True
    
    employees = Employee.objects.all()
    return render(request, 'training/certifications/employee_certs_list.html', {
        'certifications': emp_certs,
        'employees': employees,
        'selected_employee': employee,
        'selected_status': status,
    })


@login_required
def employee_certification_create(request):
    """Add certification to employee."""
    form = EmployeeCertificationForm(request.POST or None)
    if form.is_valid():
        emp_cert = form.save()
        messages.success(request, f"Certification added to {emp_cert.employee.full_name}.")
        return redirect('employee_certification_list')
    return render(request, 'training/certifications/employee_cert_form.html', {
        'form': form,
        'title': 'Add Certification to Employee'
    })


@login_required
def employee_certification_edit(request, pk):
    """Edit employee certification."""
    emp_cert = get_object_or_404(EmployeeCertification, pk=pk)
    form = EmployeeCertificationForm(request.POST or None, instance=emp_cert)
    if form.is_valid():
        form.save()
        messages.success(request, "Certification updated successfully.")
        return redirect('employee_certification_list')
    return render(request, 'training/certifications/employee_cert_form.html', {
        'form': form,
        'title': 'Edit Employee Certification',
        'emp_cert': emp_cert
    })


# ==================== DEVELOPMENT PLANS ====================

@login_required
def development_plan_list(request):
    """List all development plans."""
    plans = DevelopmentPlan.objects.all().select_related('employee', 'manager')
    status = request.GET.get('status')
    employee = request.GET.get('employee')
    
    if status:
        plans = plans.filter(status=status)
    if employee:
        plans = plans.filter(employee__id=employee)
    
    employees = Employee.objects.all()
    return render(request, 'training/development_plans/list.html', {
        'plans': plans,
        'employees': employees,
        'selected_status': status,
        'selected_employee': employee,
    })


@login_required
def development_plan_create(request):
    """Create a development plan."""
    form = DevelopmentPlanForm(request.POST or None)
    if form.is_valid():
        plan = form.save(commit=False)
        plan.manager = request.user
        plan.save()
        form.save_m2m()
        messages.success(request, f"Development plan created for {plan.employee.full_name}.")
        return redirect('development_plan_list')
    return render(request, 'training/development_plans/form.html', {
        'form': form,
        'title': 'Create Development Plan'
    })


@login_required
def development_plan_detail(request, pk):
    """View development plan details."""
    plan = get_object_or_404(DevelopmentPlan, pk=pk)
    return render(request, 'training/development_plans/detail.html', {'plan': plan})


@login_required
def development_plan_edit(request, pk):
    """Edit a development plan."""
    plan = get_object_or_404(DevelopmentPlan, pk=pk)
    form = DevelopmentPlanForm(request.POST or None, instance=plan)
    if form.is_valid():
        form.save()
        messages.success(request, "Development plan updated successfully.")
        return redirect('development_plan_detail', pk=plan.pk)
    return render(request, 'training/development_plans/form.html', {
        'form': form,
        'title': 'Edit Development Plan',
        'plan': plan
    })


@login_required
def dashboard(request):
    """Training & Development dashboard."""
    active_courses = TrainingCourse.objects.filter(status='active').count()
    upcoming_courses = TrainingCourse.objects.filter(start_date__gte=date.today()).count()
    total_employees_trained = TrainingRecord.objects.filter(status='completed').values('employee').distinct().count()
    
    # Certifications expiring soon (within 30 days)
    expiring_certs = EmployeeCertification.objects.filter(
        expiry_date__lte=date.today() + timedelta(days=30),
        expiry_date__gte=date.today(),
        status='active'
    ).select_related('employee', 'certification')
    
    # Recent trainings
    recent_trainings = TrainingRecord.objects.filter(
        status='completed'
    ).select_related('employee', 'course').order_by('-completion_date')[:5]
    
    # Active development plans
    active_plans = DevelopmentPlan.objects.filter(status='active').count()
    
    context = {
        'active_courses': active_courses,
        'upcoming_courses': upcoming_courses,
        'total_employees_trained': total_employees_trained,
        'expiring_certifications': expiring_certs.count(),
        'active_development_plans': active_plans,
        'recent_trainings': recent_trainings,
        'certifications_expiring_soon': expiring_certs,
    }
    
    return render(request, 'training/dashboard.html', context)
