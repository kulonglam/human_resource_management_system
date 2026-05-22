from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import JobPosting, Application
from .forms import JobPostingForm, ApplicationStatusForm


@login_required
def job_list(request):
    jobs = JobPosting.objects.all().order_by('-posted_on')
    return render(request, 'recruitment/job_list.html', {'jobs': jobs})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    return render(request, 'recruitment/job_detail.html', {'job': job})


@login_required
def job_create(request):
    form = JobPostingForm(request.POST or None)
    if form.is_valid():
        job = form.save()
        messages.success(request, f"Job posting '{job.title}' created successfully.")
        return redirect('job_list')
    return render(request, 'recruitment/job_form.html', {'form': form, 'title': 'Post a Job'})


@login_required
def job_edit(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    form = JobPostingForm(request.POST or None, instance=job)
    if form.is_valid():
        form.save()
        messages.success(request, f"Job posting '{job.title}' updated successfully.")
        return redirect('job_detail', pk=pk)
    return render(request, 'recruitment/job_form.html', {'form': form, 'title': 'Edit Job'})


@login_required
def application_list(request, job_pk):
    job = get_object_or_404(JobPosting, pk=job_pk)
    applications = job.applications.all().order_by('-applied_on')
    return render(request, 'recruitment/application_list.html', {
        'job': job,
        'applications': applications,
    })


@login_required
def application_update(request, pk):
    application = get_object_or_404(Application, pk=pk)
    form = ApplicationStatusForm(request.POST or None, instance=application)
    if form.is_valid():
        application.save()
        status_display = application.get_status_display()
        messages.success(request, f"Application status updated to '{status_display}'.")
        return redirect('application_list', job_pk=application.job.pk)
    return render(request, 'recruitment/application_form.html', {
        'form': form,
        'application': application,
    })
