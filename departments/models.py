from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=70)
    history = models.TextField(max_length=1000, blank=True)
    manager_name = models.CharField(max_length=100, blank=True)
    manager_contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name