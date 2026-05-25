from django.db import models
from employees.models import Employee
from django.utils import timezone

class Asset(models.Model):
    ASSET_STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('maintenance', 'In Maintenance'),
        ('retired', 'Retired'),
        ('lost', 'Lost'),
    ]
    
    asset_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_status = models.CharField(max_length=20, choices=ASSET_STATUS_CHOICES, default='available')
    serial_number = models.CharField(max_length=100, blank=True, unique=True, null=True)
    warranty_expiry = models.DateField(blank=True, null=True)
    depreciation_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.asset_code} - {self.name}"


class AssetAssignment(models.Model):
    ASSIGNMENT_STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('returned', 'Returned'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assigned_assets')
    assignment_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(blank=True, null=True)
    assignment_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default='assigned')
    condition_on_assignment = models.CharField(max_length=100, blank=True)
    condition_on_return = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assignment_date']

    def __str__(self):
        return f"{self.asset.name} assigned to {self.employee}"
