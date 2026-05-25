from django.db import models
from employees.models import Employee
from django.utils import timezone

class ExitProcess(models.Model):
    EXIT_REASON_CHOICES = [
        ('resignation', 'Resignation'),
        ('termination', 'Termination'),
        ('retirement', 'Retirement'),
        ('contract_end', 'Contract End'),
        ('redundancy', 'Redundancy'),
        ('death', 'Death'),
    ]
    
    EXIT_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='exit_process')
    exit_date = models.DateField()
    reason = models.CharField(max_length=50, choices=EXIT_REASON_CHOICES)
    status = models.CharField(max_length=20, choices=EXIT_STATUS_CHOICES, default='initiated')
    last_working_day = models.DateField(blank=True, null=True)
    notice_period_days = models.IntegerField(default=30)
    final_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    exit_interview_completed = models.BooleanField(default=False)
    exit_interview_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Exit Process for {self.employee}"


class ExitChecklist(models.Model):
    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('not_applicable', 'Not Applicable'),
    ]
    
    exit_process = models.ForeignKey(ExitProcess, on_delete=models.CASCADE, related_name='checklist_items')
    item_name = models.CharField(max_length=200)
    responsible_person = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='pending')
    completion_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exit_process', 'created_at']

    def __str__(self):
        return f"{self.item_name} - {self.exit_process}"
