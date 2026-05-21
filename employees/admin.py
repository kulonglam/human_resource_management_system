from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'job_title', 'department', 'date_joined', 'is_active']
    list_filter = ['department', 'gender', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'job_title']
