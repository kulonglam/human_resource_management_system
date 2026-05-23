from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from employees.models import Employee
from accounts.models import CustomUser


class Skill(models.Model):
    """Skills catalog for tracking employee competencies."""
    PROFICIENCY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('technical', 'Technical'),
            ('soft_skills', 'Soft Skills'),
            ('management', 'Management'),
            ('other', 'Other'),
        ]
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class EmployeeSkill(models.Model):
    """Track employee skills and proficiency levels."""
    PROFICIENCY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='skills'
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name='employees'
    )
    proficiency_level = models.CharField(max_length=15, choices=PROFICIENCY_LEVELS)
    years_of_experience = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    verified = models.BooleanField(default=False, help_text="Verified by manager/admin")
    verified_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_skills'
    )
    verified_date = models.DateField(null=True, blank=True)
    acquired_date = models.DateField(help_text="When skill was acquired")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('employee', 'skill')
        ordering = ['skill__category', 'skill__name']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.skill.name} ({self.proficiency_level})"


class TrainingCourse(models.Model):
    """Training courses/programs available."""
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('technical', 'Technical'),
            ('soft_skills', 'Soft Skills'),
            ('compliance', 'Compliance'),
            ('leadership', 'Leadership'),
            ('other', 'Other'),
        ]
    )
    provider = models.CharField(max_length=200, help_text="Training provider/instructor")
    duration_hours = models.PositiveIntegerField(help_text="Duration in hours")
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=200, blank=True, help_text="Physical or online location")
    is_online = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='planned')
    related_skills = models.ManyToManyField(Skill, blank=True, related_name='courses')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='courses_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def participants_count(self):
        return self.trainings.filter(status='enrolled').count()


class TrainingRecord(models.Model):
    """Employee training enrollment and completion records."""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='trainings'
    )
    course = models.ForeignKey(
        TrainingCourse, on_delete=models.CASCADE, related_name='trainings'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='enrolled')
    completion_date = models.DateField(null=True, blank=True)
    
    # Assessment
    score = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Assessment score (0-100)"
    )
    feedback = models.TextField(blank=True, help_text="Trainer feedback")
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_number = models.CharField(max_length=100, blank=True, unique=True)
    
    enrolled_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('employee', 'course')
        ordering = ['-enrolled_date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.course.title} ({self.status})"


class Certification(models.Model):
    """Professional certifications."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('pending_renewal', 'Pending Renewal'),
    ]
    
    name = models.CharField(max_length=200)
    issuing_body = models.CharField(max_length=200, help_text="Organization issuing the certification")
    description = models.TextField(blank=True)
    validity_years = models.PositiveIntegerField(help_text="How many years the cert is valid")
    required_for_roles = models.CharField(
        max_length=255, blank=True,
        help_text="Comma-separated job titles that require this certification"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EmployeeCertification(models.Model):
    """Track employee certifications."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('pending_renewal', 'Pending Renewal'),
    ]
    
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='certifications'
    )
    certification = models.ForeignKey(
        Certification, on_delete=models.CASCADE, related_name='employees'
    )
    issue_date = models.DateField()
    expiry_date = models.DateField()
    certificate_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('employee', 'certification')
        ordering = ['-expiry_date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.certification.name}"
    
    @property
    def days_until_expiry(self):
        from datetime import date
        delta = self.expiry_date - date.today()
        return delta.days
    
    @property
    def is_expiring_soon(self):
        return 0 < self.days_until_expiry <= 30


class DevelopmentPlan(models.Model):
    """Employee development/training plans."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='development_plans'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    goals = models.TextField(help_text="Development goals and objectives")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    
    # Tracking
    manager = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='development_plans_managed'
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall progress percentage (0-100)"
    )
    
    # Associated trainings
    planned_courses = models.ManyToManyField(TrainingCourse, blank=True, related_name='development_plans')
    target_skills = models.ManyToManyField(Skill, blank=True, related_name='development_plans')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"
