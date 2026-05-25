from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Discipline, DisciplineAppeal
from .forms import DisciplineForm, DisciplineStatusForm, DisciplineAppealForm, DisciplineAppealReviewForm

@login_required
def discipline_list(request):
    disciplines = Discipline.objects.all()
    return render(request, 'discipline/list.html', {'disciplines': disciplines})

@login_required
def discipline_detail(request, pk):
    discipline = get_object_or_404(Discipline, pk=pk)
    appeal = discipline.appeal if hasattr(discipline, 'appeal') else None
    return render(request, 'discipline/detail.html', {'discipline': discipline, 'appeal': appeal})

@login_required
def discipline_create(request):
    if request.method == 'POST':
        form = DisciplineForm(request.POST, request.FILES)
        if form.is_valid():
            discipline = form.save(commit=False)
            discipline.issued_by = request.user.employee
            discipline.save()
            messages.success(request, 'Discipline record created successfully')
            return redirect('discipline_list')
    else:
        form = DisciplineForm()
    return render(request, 'discipline/form.html', {'form': form, 'title': 'Create Discipline Record'})

@login_required
def discipline_update(request, pk):
    discipline = get_object_or_404(Discipline, pk=pk)
    if request.method == 'POST':
        form = DisciplineStatusForm(request.POST, instance=discipline)
        if form.is_valid():
            form.save()
            messages.success(request, 'Discipline record updated')
            return redirect('discipline_detail', pk=discipline.pk)
    else:
        form = DisciplineStatusForm(instance=discipline)
    return render(request, 'discipline/status_form.html', {'form': form, 'discipline': discipline})

@login_required
def appeal_create(request, discipline_id):
    discipline = get_object_or_404(Discipline, pk=discipline_id)
    if request.method == 'POST':
        form = DisciplineAppealForm(request.POST, request.FILES)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.discipline = discipline
            appeal.save()
            discipline.status = 'appealed'
            discipline.save()
            messages.success(request, 'Appeal submitted successfully')
            return redirect('discipline_detail', pk=discipline.pk)
    else:
        form = DisciplineAppealForm()
    return render(request, 'discipline/appeal_form.html', {'form': form, 'discipline': discipline})

@login_required
def appeal_review(request, pk):
    appeal = get_object_or_404(DisciplineAppeal, pk=pk)
    if request.method == 'POST':
        form = DisciplineAppealReviewForm(request.POST, instance=appeal)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.reviewed_by = request.user.employee
            appeal.save()
            messages.success(request, 'Appeal reviewed')
            return redirect('discipline_detail', pk=appeal.discipline.pk)
    else:
        form = DisciplineAppealReviewForm(instance=appeal)
    return render(request, 'discipline/appeal_review.html', {'form': form, 'appeal': appeal})
