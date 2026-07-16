from django.db import models

from accounts.models import CustomUser
from employees.models import Employee


class HRDocument(models.Model):
    CATEGORY_CHOICES = [
        ('contract', 'Employment Contract'),
        ('policy', 'HR Policy'),
        ('offer_letter', 'Offer Letter'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='hr_documents/')
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='documents',
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    requires_acknowledgement = models.BooleanField(default=False)
    expires_at = models.DateField(null=True, blank=True)
    legal_hold = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} (v{self.version})'


class DocumentAcknowledgement(models.Model):
    document = models.ForeignKey(
        HRDocument, on_delete=models.CASCADE, related_name='acknowledgements',
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='document_acknowledgements',
    )
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        unique_together = ('document', 'employee')
        ordering = ['-acknowledged_at']

    def __str__(self):
        return f'{self.employee} acknowledged {self.document.title}'


class DocumentAccessRule(models.Model):
    """Role-based document category access matrix."""

    role = models.ForeignKey('accounts.Role', on_delete=models.CASCADE, related_name='document_access_rules')
    category = models.CharField(max_length=20, choices=HRDocument.CATEGORY_CHOICES)
    can_view = models.BooleanField(default=True)
    can_upload = models.BooleanField(default=False)

    class Meta:
        unique_together = ('role', 'category')
        ordering = ['role__name', 'category']

    def __str__(self):
        return f'{self.role} — {self.category}'
