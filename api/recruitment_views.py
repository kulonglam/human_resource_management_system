from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recruitment.models import Application, JobPipelineStage, JobPosting
from recruitment.services import ensure_default_pipeline_stages


class RecruitmentSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        job_id = request.query_params.get('job')
        status_filter = request.query_params.get('status')
        search = (request.query_params.get('q') or '').strip()

        apps = Application.objects.select_related('job', 'current_stage')
        if job_id:
            apps = apps.filter(job_id=job_id)
        if status_filter:
            apps = apps.filter(status=status_filter)
        if search:
            apps = apps.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(job__title__icontains=search)
            )

        statuses = ['received', 'shortlisted', 'interviewed', 'offer', 'hired', 'rejected']
        all_apps = Application.objects.select_related('job')
        by_status = {s: all_apps.filter(status=s).count() for s in statuses}

        active = all_apps.exclude(status__in=['hired', 'rejected'])
        if active.exists():
            total_days = sum((timezone.now() - app.applied_on).days for app in active)
            avg_days = round(total_days / active.count(), 1)
        else:
            avg_days = 0

        hired = all_apps.filter(status='hired', hired_at__isnull=False)
        if hired.exists():
            hire_days = sum((app.hired_at - app.applied_on).days for app in hired)
            avg_time_to_hire = round(hire_days / hired.count(), 1)
        else:
            avg_time_to_hire = 0

        funnel_stages = ['received', 'shortlisted', 'interviewed', 'offer', 'hired']
        funnel = []
        for idx, stage in enumerate(funnel_stages):
            count = by_status.get(stage, 0)
            if idx == 0:
                prev = all_apps.count() or 1
            else:
                prev = by_status.get(funnel_stages[idx - 1], 0) or 1
            funnel.append({
                'key': stage,
                'label': stage.replace('_', ' ').title(),
                'count': count,
                'conversion_pct': round((count / prev) * 100, 1) if prev else 0,
            })

        by_source = {}
        for row in all_apps.values('source').distinct():
            key = row['source']
            by_source[key] = all_apps.filter(source=key).count()

        pipeline_stages = []
        if job_id:
            job = JobPosting.objects.filter(pk=job_id).first()
            if job:
                ensure_default_pipeline_stages(job)
                pipeline_stages = list(
                    job.pipeline_stages.exclude(stage_type='rejected').values(
                        'id', 'key', 'label', 'order', 'stage_type',
                    ),
                )
        if not pipeline_stages:
            pipeline_stages = [
                {'id': None, 'key': k, 'label': k.replace('_', ' ').title(), 'order': i, 'stage_type': 'hired' if k == 'hired' else 'active'}
                for i, k in enumerate(['received', 'shortlisted', 'interviewed', 'offer', 'hired'])
            ]

        pipeline = [
            {
                'id': app.id,
                'full_name': f'{app.first_name} {app.last_name}',
                'email': app.email,
                'job_id': app.job_id,
                'job_title': app.job.title,
                'status': app.status,
                'stage_id': app.current_stage_id,
                'stage_key': app.current_stage.key if app.current_stage else app.status,
                'source': app.source,
                'rating': app.rating,
                'applied_on': app.applied_on,
            }
            for app in apps.order_by('-applied_on')
        ]

        open_jobs = JobPosting.objects.filter(is_open=True)
        jobs = [
            {'id': j.id, 'title': j.title, 'department': j.department, 'application_count': j.applications.count()}
            for j in open_jobs.order_by('-posted_on')
        ]

        return Response({
            'open_jobs': open_jobs.count(),
            'total_jobs': JobPosting.objects.count(),
            'total_applications': all_apps.count(),
            'pending_review': by_status.get('received', 0),
            'by_status': by_status,
            'by_source': by_source,
            'avg_days_in_pipeline': avg_days,
            'avg_time_to_hire': avg_time_to_hire,
            'funnel': funnel,
            'pipeline': pipeline,
            'pipeline_stages': pipeline_stages,
            'jobs': jobs,
        })
