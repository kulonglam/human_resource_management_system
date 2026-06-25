from django.db import migrations

DEFAULT_STAGES = [
    ('received', 'Received', 0, 'active'),
    ('shortlisted', 'Shortlisted', 1, 'active'),
    ('interviewed', 'Interviewed', 2, 'active'),
    ('offer', 'Offer', 3, 'active'),
    ('hired', 'Hired', 4, 'hired'),
    ('rejected', 'Rejected', 5, 'rejected'),
]

OFFER_TEMPLATE_BODY = """Dear {{candidate_name}},

We are pleased to offer you the position of {{job_title}} in our {{department}} department at {{company}}.

Compensation: {{salary}} per annum
Proposed start date: {{start_date}}

We look forward to welcoming you to the team.

Sincerely,
Human Resources"""


def seed_enterprise_data(apps, schema_editor):
    JobPosting = apps.get_model('recruitment', 'JobPosting')
    JobPipelineStage = apps.get_model('recruitment', 'JobPipelineStage')
    Application = apps.get_model('recruitment', 'Application')
    OfferTemplate = apps.get_model('recruitment', 'OfferTemplate')

    OfferTemplate.objects.get_or_create(
        name='Standard offer letter',
        defaults={'body': OFFER_TEMPLATE_BODY, 'is_active': True},
    )

    for job in JobPosting.objects.all():
        if not JobPipelineStage.objects.filter(job=job).exists():
            JobPipelineStage.objects.bulk_create([
                JobPipelineStage(
                    job=job,
                    key=key,
                    label=label,
                    order=order,
                    stage_type=stage_type,
                )
                for key, label, order, stage_type in DEFAULT_STAGES
            ])

    for app in Application.objects.filter(current_stage__isnull=True).select_related('job'):
        stage = JobPipelineStage.objects.filter(job=app.job, key=app.status).first()
        if not stage:
            stage = JobPipelineStage.objects.filter(job=app.job, key='received').first()
        if stage:
            app.current_stage_id = stage.pk
            app.save(update_fields=['current_stage_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0003_offertemplate_application_eeo_disability_status_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_enterprise_data, migrations.RunPython.noop),
    ]
