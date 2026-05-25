from django.db import models
from employees.models import Employee
from django.utils import timezone

class Discipline(models.Model):
    DISCIPLINE_TYPE_CHOICES = [
        ('verbal_warning', 'Verbal Warning'),
        ('written_warning', 'Written Warning'),
        ('suspension', 'Suspension'),
        ('final_warning', 'Final Warning'),
        ('termination', 'Termination'),
    ]
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('under_review', 'Under Review'),
        ('issued', 'Issued'),
        ('appealed', 'Appealed'),
        ('closed', 'Closed'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='discipline_records')
    discipline_type = models.CharField(max_length=50, choices=DISCIPLINE_TYPE_CHOICES)
    reason = models.CharField(max_length=200)
    detailed_reason = models.TextField()
    incident_date = models.DateField()
    issued_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    issued_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='issued_disciplines')
    next_review_date = models.DateField(blank=True, null=True)
    documents = models.FileField(upload_to='discipline_documents/', blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.get_discipline_type_display()}"


class DisciplineAppeal(models.Model):
    APPEAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('dismissed', 'Dismissed'),
    ]
    
    discipline = models.OneToOneField(Discipline, on_delete=models.CASCADE, related_name='appeal')
    appeal_date = models.DateField()
    appeal_reason = models.TextField()
    supporting_documents = models.FileField(upload_to='appeal_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=APPEAL_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_appeals')
    review_date = models.DateField(blank=True, null=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appeal for {self.discipline}"
