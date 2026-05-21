from django.contrib import admin
from .models import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'manager_name', 'history', 'manager_contact', 'created_at']
    search_fields = ['name', 'location', 'manager__first_name', 'manager__last_name']
