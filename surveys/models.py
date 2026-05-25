from django.db import models
from employees.models import Employee
from django.utils import timezone

class Survey(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    survey_type = models.CharField(max_length=50, choices=[('feedback', '360 Feedback'), ('satisfaction', 'Satisfaction'), ('engagement', 'Engagement')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='created_surveys')
    start_date = models.DateField()
    end_date = models.DateField()
    is_anonymous = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SurveyQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('rating', 'Rating (1-5)'),
        ('multiple_choice', 'Multiple Choice'),
        ('checkbox', 'Checkbox'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    options = models.TextField(blank=True, help_text='For multiple choice/checkbox, separate options with commas')
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['survey', 'order']

    def __str__(self):
        return self.question_text[:100]


class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='survey_responses')
    subject = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='received_feedback')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name='responses')
    response_text = models.TextField(blank=True)
    response_rating = models.IntegerField(blank=True, null=True, choices=[(i, str(i)) for i in range(1, 6)])
    response_selected = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Response to {self.survey.title}"
