from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from employees.models import Employee
from accounts.models import CustomUser


class PerformanceGoal(models.Model):
    """Track employee performance goals and objectives."""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='performance_goals'
    )
    goal_title = models.CharField(max_length=200)
    goal_description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    target_metric = models.CharField(max_length=200, help_text="How will success be measured?")
    priority = models.CharField(
        max_length=10, 
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='not_started')
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress percentage (0-100)"
    )
    notes = models.TextField(blank=True)
    set_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='goals_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.goal_title}"


class PerformanceAppraisal(models.Model):
    """Performance evaluation/appraisal records."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
    ]
    
    RATING_CHOICES = [
        (1, 'Needs Improvement'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='appraisals'
    )
    appraisal_period_start = models.DateField()
    appraisal_period_end = models.DateField()
    appraiser = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='appraisals_given'
    )
    
    # Performance Ratings
    job_knowledge = models.IntegerField(choices=RATING_CHOICES, help_text="Knowledge of job responsibilities")
    work_quality = models.IntegerField(choices=RATING_CHOICES, help_text="Quality of work output")
    productivity = models.IntegerField(choices=RATING_CHOICES, help_text="Productivity and efficiency")
    communication = models.IntegerField(choices=RATING_CHOICES, help_text="Communication skills")
    teamwork = models.IntegerField(choices=RATING_CHOICES, help_text="Collaboration and teamwork")
    initiative = models.IntegerField(choices=RATING_CHOICES, help_text="Initiative and innovation")
    reliability = models.IntegerField(choices=RATING_CHOICES, help_text="Attendance and punctuality")
    
    # Overall assessment
    overall_rating = models.IntegerField(
        choices=RATING_CHOICES,
        editable=False,
        help_text="Auto-calculated average rating"
    )
    
    # Comments and feedback
    strengths = models.TextField(help_text="Employee strengths")
    areas_for_improvement = models.TextField(help_text="Areas to improve")
    reviewer_comments = models.TextField(blank=True, help_text="Additional reviewer comments")
    
    # Goals and development
    next_goals = models.TextField(help_text="Recommended goals for next period")
    training_needs = models.TextField(blank=True, help_text="Training and development needs")
    
    # Meta
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-appraisal_period_end']
        unique_together = ('employee', 'appraisal_period_start', 'appraisal_period_end')
    
    def save(self, *args, **kwargs):
        # Calculate overall rating as average
        ratings = [
            self.job_knowledge, self.work_quality, self.productivity,
            self.communication, self.teamwork, self.initiative, self.reliability
        ]
        self.overall_rating = sum(ratings) // len(ratings)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.appraisal_period_start} to {self.appraisal_period_end}"


class FeedbackRound(models.Model):
    """360-degree feedback round setup."""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planned')
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='feedback_rounds_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class FeedbackRequest(models.Model):
    """360-degree feedback request from one person to another."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    feedback_round = models.ForeignKey(
        FeedbackRound, on_delete=models.CASCADE, related_name='feedback_requests'
    )
    recipient = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='feedback_received'
    )
    feedback_giver = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='feedback_given'
    )
    giver_type = models.CharField(
        max_length=20,
        choices=[
            ('manager', 'Manager'),
            ('peer', 'Peer'),
            ('direct_report', 'Direct Report'),
            ('other', 'Other'),
        ],
        help_text="Relationship of feedback giver to recipient"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('feedback_round', 'recipient', 'feedback_giver')
    
    def __str__(self):
        return f"Feedback for {self.recipient.full_name} from {self.feedback_giver.username} ({self.giver_type})"


class Feedback(models.Model):
    """360-degree feedback submission."""
    RATING_CHOICES = [
        (1, 'Strongly Disagree'),
        (2, 'Disagree'),
        (3, 'Neutral'),
        (4, 'Agree'),
        (5, 'Strongly Agree'),
    ]
    
    request = models.OneToOneField(
        FeedbackRequest, on_delete=models.CASCADE, related_name='feedback'
    )
    
    # Competency ratings
    communication = models.IntegerField(choices=RATING_CHOICES, help_text="Effective communication")
    leadership = models.IntegerField(choices=RATING_CHOICES, help_text="Leadership skills")
    teamwork = models.IntegerField(choices=RATING_CHOICES, help_text="Teamwork and collaboration")
    reliability = models.IntegerField(choices=RATING_CHOICES, help_text="Reliability and accountability")
    initiative = models.IntegerField(choices=RATING_CHOICES, help_text="Initiative and proactivity")
    problem_solving = models.IntegerField(choices=RATING_CHOICES, help_text="Problem-solving ability")
    
    # Comments
    strengths = models.TextField(blank=True, help_text="What are this person's key strengths?")
    areas_for_improvement = models.TextField(blank=True, help_text="Areas for development")
    additional_comments = models.TextField(blank=True)
    
    is_anonymous = models.BooleanField(default=False, help_text="Submit feedback anonymously")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feedback for {self.request.recipient.full_name} - {self.created_at.date()}"


class FeedbackSummary(models.Model):
    """Summary/analysis of 360-degree feedback for an employee."""
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name='feedback_summary'
    )
    feedback_round = models.ForeignKey(
        FeedbackRound, on_delete=models.CASCADE, related_name='summaries'
    )
    
    # Average ratings
    avg_communication = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    avg_leadership = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    avg_teamwork = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    avg_reliability = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    avg_initiative = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    avg_problem_solving = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Synthesis
    key_strengths = models.TextField(help_text="Summary of common strengths from feedback")
    development_areas = models.TextField(help_text="Summary of common development areas")
    recommendations = models.TextField(blank=True, help_text="Recommendations based on feedback")
    
    total_responses = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('employee', 'feedback_round')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.feedback_round.name} Summary"
