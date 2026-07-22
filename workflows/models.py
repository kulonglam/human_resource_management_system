from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from accounts.models import CustomUser
from accounts.tenancy import organization_fk


class ApprovalWorkflow(models.Model):
    WORKFLOW_TYPES = [
        ('leave', 'Leave'),
        ('expense', 'Expense'),
        ('recruitment', 'Recruitment'),
    ]

    name = models.CharField(max_length=100)
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPES)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    organization = organization_fk(related_name='approval_workflows')
    extra_step_min_days = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Leave: require HR step when duration >= this many days',
    )
    extra_step_min_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Expense: require HR step when amount >= this value',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workflow_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_workflow_type_display()})'


class ApprovalStep(models.Model):
    APPROVER_TYPES = [
        ('manager', 'Direct Manager'),
        ('admin', 'HR Administrator'),
    ]

    workflow = models.ForeignKey(
        ApprovalWorkflow, on_delete=models.CASCADE, related_name='steps',
    )
    step_order = models.PositiveSmallIntegerField()
    label = models.CharField(max_length=100)
    approver_type = models.CharField(max_length=20, choices=APPROVER_TYPES)

    class Meta:
        ordering = ['workflow', 'step_order']
        unique_together = [('workflow', 'step_order')]

    def __str__(self):
        return f'{self.workflow.name} — Step {self.step_order}: {self.label}'


class ApprovalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.PROTECT, related_name='requests')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_step_order = models.PositiveSmallIntegerField(default=1)
    submitted_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_approvals',
    )
    submitted_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status', '-submitted_at']),
        ]

    def __str__(self):
        return f'Approval #{self.pk} — {self.status}'


class ApprovalDecision(models.Model):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='decisions')
    step_order = models.PositiveSmallIntegerField()
    step_label = models.CharField(max_length=100)
    decided_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approval_decisions',
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['request', 'step_order']

    def __str__(self):
        return f'{self.step_label} — {self.decision}'
