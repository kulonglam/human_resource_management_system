import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from departments.models import Department
from employees.models import Employee

from .models import (
    Application,
    HireOnboarding,
    JobOffer,
    JobPipelineStage,
    JobPosting,
    OfferTemplate,
)

DEFAULT_PIPELINE_STAGES = [
    ('received', 'Received', 0, 'active'),
    ('shortlisted', 'Shortlisted', 1, 'active'),
    ('interviewed', 'Interviewed', 2, 'active'),
    ('offer', 'Offer', 3, 'active'),
    ('hired', 'Hired', 4, 'hired'),
    ('rejected', 'Rejected', 5, 'rejected'),
]

STAGE_KEY_TO_STATUS = {
    'received': 'received',
    'shortlisted': 'shortlisted',
    'interviewed': 'interviewed',
    'offer': 'offer',
    'hired': 'hired',
    'rejected': 'rejected',
}


def ensure_default_pipeline_stages(job):
    if job.pipeline_stages.exists():
        return
    JobPipelineStage.objects.bulk_create([
        JobPipelineStage(
            job=job,
            key=key,
            label=label,
            order=order,
            stage_type=stage_type,
        )
        for key, label, order, stage_type in DEFAULT_PIPELINE_STAGES
    ])


def initial_stage_for_job(job):
    ensure_default_pipeline_stages(job)
    return job.pipeline_stages.filter(stage_type='active').order_by('order').first()


def sync_application_stage(application, stage):
    application.current_stage = stage
    if stage.stage_type == 'hired':
        application.status = 'hired'
        if not application.hired_at:
            application.hired_at = timezone.now()
    elif stage.stage_type == 'rejected':
        application.status = 'rejected'
    else:
        application.status = STAGE_KEY_TO_STATUS.get(stage.key, application.status)
    application.save(update_fields=['current_stage', 'status', 'hired_at'])


def render_offer_body(template_body, offer, application):
    company = 'Organization'
    return (
        template_body
        .replace('{{candidate_name}}', f'{application.first_name} {application.last_name}')
        .replace('{{job_title}}', offer.job_title)
        .replace('{{department}}', offer.department)
        .replace('{{salary}}', f'{offer.currency} {offer.salary:,.2f}')
        .replace('{{start_date}}', str(offer.start_date))
        .replace('{{company}}', company)
    )


def build_offer_from_template(template, application, created_by, **overrides):
    offer = JobOffer(
        application=application,
        template=template,
        job_title=overrides.get('job_title', application.job.title),
        department=overrides.get('department', application.job.department),
        salary=overrides.get('salary', 0),
        currency=overrides.get('currency', 'UGX'),
        start_date=overrides.get('start_date', timezone.now().date() + timedelta(days=30)),
        created_by=created_by,
        body='',
    )
    offer.body = render_offer_body(template.body, offer, application)
    for field in ('job_title', 'department', 'salary', 'currency', 'start_date', 'body'):
        if field in overrides:
            setattr(offer, field, overrides[field])
    return offer


def create_hire_onboarding(application, start_date=None, salary=None, job_title=None):
    onboarding, created = HireOnboarding.objects.get_or_create(
        application=application,
        defaults={
            'job_title': job_title or application.job.title,
            'department_name': application.job.department,
            'start_date': start_date or timezone.now().date(),
            'salary': salary or 0,
        },
    )
    if not created and start_date:
        onboarding.start_date = start_date
        if salary is not None:
            onboarding.salary = salary
        onboarding.save(update_fields=['start_date', 'salary'])
    return onboarding


def complete_hire_onboarding(onboarding, hr_user, employee_data):
    """Create employee record from onboarding + HR-supplied fields."""
    with transaction.atomic():
        onboarding = HireOnboarding.objects.select_for_update().select_related(
            'application', 'application__job',
        ).get(pk=onboarding.pk)
        if onboarding.status == 'completed':
            raise ValueError('Onboarding already completed.')

        application = Application.objects.select_for_update().get(pk=onboarding.application_id)
        department = employee_data.get('department')
        if isinstance(department, int):
            department = Department.objects.filter(pk=department).first()

        employee = Employee.objects.create(
            first_name=application.first_name,
            last_name=application.last_name,
            email=application.email,
            mobile=employee_data.get('mobile', application.phone),
            date_of_birth=employee_data['date_of_birth'],
            gender=employee_data.get('gender', 'Other'),
            address=employee_data.get('address', 'TBD'),
            emergency_contact=employee_data.get('emergency_contact', application.phone),
            job_title=employee_data.get('job_title', onboarding.job_title)[:20],
            department=department,
            date_joined=employee_data.get('date_joined', onboarding.start_date),
            account_number=employee_data.get('account_number', '0000000000'),
            bank=employee_data.get('bank', 'TBD'),
            salary=employee_data.get('salary', onboarding.salary),
        )

        application.employee = employee
        application.save(update_fields=['employee'])

        onboarding.employee = employee
        onboarding.status = 'completed'
        onboarding.completed_at = timezone.now()
        onboarding.save(update_fields=['employee', 'status', 'completed_at'])

    return employee


def generate_interview_ics(interview):
    application = interview.application
    uid = interview.calendar_uid or str(uuid.uuid4())
    if not interview.calendar_uid:
        interview.calendar_uid = uid
        interview.save(update_fields=['calendar_uid'])

    start = interview.scheduled_at.strftime('%Y%m%dT%H%M%S')
    end_dt = interview.scheduled_at + timedelta(minutes=interview.duration_minutes)
    end = end_dt.strftime('%Y%m%dT%H%M%S')
    summary = f'Interview: {application.first_name} {application.last_name} — {application.job.title}'
    location = interview.location or 'TBD'
    description = interview.notes or f'Interview with {application.first_name} {application.last_name}'

    return '\r\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//HRMIS//Recruitment//EN',
        'BEGIN:VEVENT',
        f'UID:{uid}@hrmis',
        f'DTSTAMP:{timezone.now().strftime("%Y%m%dT%H%M%SZ")}',
        f'DTSTART:{start}',
        f'DTEND:{end}',
        f'SUMMARY:{summary}',
        f'DESCRIPTION:{description}',
        f'LOCATION:{location}',
        'END:VEVENT',
        'END:VCALENDAR',
    ])


def backfill_job_stages():
    for job in JobPosting.objects.all():
        ensure_default_pipeline_stages(job)


def backfill_application_stages():
    for app in Application.objects.select_related('job').filter(current_stage__isnull=True):
        stage = app.job.pipeline_stages.filter(key=app.status).first()
        if not stage:
            stage = initial_stage_for_job(app.job)
        if stage:
            app.current_stage = stage
            app.save(update_fields=['current_stage'])


def update_application_after_save(*, application, old_status, previous_status_label):
    """Side-effects when an application status changes on update."""
    from api.notifications import notify_application_status

    if old_status != application.status:
        if application.status == 'hired' and not application.hired_at:
            application.hired_at = timezone.now()
            application.save(update_fields=['hired_at'])
        notify_application_status(application, previous_status_label)
    return application


def move_application_to_stage(*, application, stage):
    """Move application to a pipeline stage; may trigger hire onboarding."""
    with transaction.atomic():
        application = Application.objects.select_for_update().select_related('job').get(
            pk=application.pk,
        )
        sync_application_stage(application, stage)
        if stage.stage_type == 'hired':
            create_hire_onboarding(application)
    return application


def after_interview_created(*, interview):
    """Align application status when an interview is scheduled."""
    with transaction.atomic():
        application = Application.objects.select_for_update().select_related('job').get(
            pk=interview.application_id,
        )
        stage = application.job.pipeline_stages.filter(key='interviewed').first()
        if stage:
            sync_application_stage(application, stage)
        elif application.status in ('received', 'shortlisted'):
            application.status = 'interviewed'
            application.save(update_fields=['status'])
    return interview


def create_offer_from_template_data(*, template, application, created_by, **data):
    """Build and persist a job offer from a template."""
    offer = build_offer_from_template(
        template,
        application,
        created_by,
        salary=data['salary'],
        start_date=data['start_date'],
        currency=data.get('currency', 'UGX'),
        job_title=data.get('job_title') or application.job.title,
        department=data.get('department') or application.job.department,
    )
    offer.save()
    return offer


def submit_job_offer(offer):
    with transaction.atomic():
        offer = JobOffer.objects.select_for_update().get(pk=offer.pk)
        offer.status = 'pending_approval'
        offer.save(update_fields=['status', 'updated_at'])
    return offer


def approve_job_offer(offer):
    with transaction.atomic():
        offer = JobOffer.objects.select_for_update().get(pk=offer.pk)
        if offer.status != 'pending_approval':
            raise ValueError('Offer is not pending approval.')
        offer.status = 'approved'
        offer.save(update_fields=['status', 'updated_at'])
    return offer


def send_job_offer(offer):
    with transaction.atomic():
        offer = JobOffer.objects.select_for_update().select_related(
            'application', 'application__job',
        ).get(pk=offer.pk)
        if offer.status not in ('approved', 'draft'):
            raise ValueError('Offer must be approved before sending.')
        offer.status = 'sent'
        offer.sent_at = timezone.now()
        offer.save(update_fields=['status', 'sent_at', 'updated_at'])
        stage = offer.application.job.pipeline_stages.filter(key='offer').first()
        if stage:
            application = Application.objects.select_for_update().get(pk=offer.application_id)
            sync_application_stage(application, stage)
    return offer
