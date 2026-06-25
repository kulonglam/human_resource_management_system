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
    uploaded_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} (v{self.version})'
