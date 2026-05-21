from django.db import models
from employees.models import Employee

class Kin(models.Model):
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name='kin'
    )
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    address = models.CharField(max_length=100)
    occupation = models.CharField(max_length=20)
    mobile = models.CharField(max_length=14)
    relationship = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Kin of {self.employee})"