from django.conf import settings
from django.db import models


class JobPosting(models.Model):
    title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField()
    deadline = models.DateField()
    is_open = models.BooleanField(default=True)
    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class JobPipelineStage(models.Model):
    STAGE_TYPES = [
        ('active', 'Active'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='pipeline_stages')
    key = models.SlugField(max_length=40)
    label = models.CharField(max_length=60)
    order = models.PositiveSmallIntegerField(default=0)
    stage_type = models.CharField(max_length=10, choices=STAGE_TYPES, default='active')

    class Meta:
        ordering = ['order']
        unique_together = [('job', 'key')]

    def __str__(self):
        return f'{self.job.title} — {self.label}'


class HiringTeamMember(models.Model):
    ROLE_CHOICES = [
        ('recruiter', 'Recruiter'),
        ('hiring_manager', 'Hiring Manager'),
        ('interviewer', 'Interviewer'),
        ('coordinator', 'Coordinator'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='hiring_team')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hiring_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        unique_together = [('job', 'user', 'role')]

    def __str__(self):
        return f'{self.user} ({self.role}) on {self.job_id}'


class ScorecardCriterion(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='scorecard_criteria')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    weight = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Application(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('shortlisted', 'Shortlisted'),
        ('interviewed', 'Interviewed'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    ]
    SOURCE_CHOICES = [
        ('careers_portal', 'Careers portal'),
        ('referral', 'Referral'),
        ('linkedin', 'LinkedIn'),
        ('agency', 'Agency'),
        ('manual', 'Manual'),
        ('other', 'Other'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    current_stage = models.ForeignKey(
        JobPipelineStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='recruitment/resumes/', null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='received')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    hired_at = models.DateTimeField(null=True, blank=True)
    applied_on = models.DateTimeField(auto_now_add=True)
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hire_applications',
    )
    # Voluntary EEO (self-reported)
    eeo_gender = models.CharField(max_length=30, blank=True)
    eeo_ethnicity = models.CharField(max_length=60, blank=True)
    eeo_veteran_status = models.CharField(max_length=40, blank=True)
    eeo_disability_status = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} → {self.job.title}"


class ApplicationNote(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='application_notes',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Note on {self.application_id}'


class Interview(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No show'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    location = models.CharField(max_length=255, blank=True)
    interviewer_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    calendar_uid = models.CharField(max_length=64, blank=True)
    external_calendar_url = models.URLField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='scheduled_interviews',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'Interview for {self.application_id}'


class ApplicationScorecard(models.Model):
    RECOMMENDATION_CHOICES = [
        ('strong_yes', 'Strong Yes'),
        ('yes', 'Yes'),
        ('neutral', 'Neutral'),
        ('no', 'No'),
        ('strong_no', 'Strong No'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='scorecards')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scorecards')
    overall_recommendation = models.CharField(max_length=15, choices=RECOMMENDATION_CHOICES)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('application', 'reviewer')]

    def __str__(self):
        return f'Scorecard {self.application_id} by {self.reviewer_id}'


class ScorecardRating(models.Model):
    scorecard = models.ForeignKey(ApplicationScorecard, on_delete=models.CASCADE, related_name='ratings')
    criterion = models.ForeignKey(ScorecardCriterion, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = [('scorecard', 'criterion')]


class OfferTemplate(models.Model):
    name = models.CharField(max_length=100)
    body = models.TextField(
        help_text='Use placeholders: {{candidate_name}}, {{job_title}}, {{department}}, {{salary}}, {{start_date}}, {{company}}',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class JobOffer(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('withdrawn', 'Withdrawn'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='offers')
    template = models.ForeignKey(OfferTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    start_date = models.DateField()
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sent_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signer_name = models.CharField(max_length=100, blank=True)
    signer_ip = models.GenericIPAddressField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_offers',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Offer for {self.application_id} ({self.status})'


class HireOnboarding(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='onboarding')
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_records',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    job_title = models.CharField(max_length=100)
    department_name = models.CharField(max_length=100)
    start_date = models.DateField()
    salary = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Onboarding for {self.application_id}'
