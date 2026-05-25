from django.contrib import admin
from .models import Benefit, EmployeeBenefit

@admin.register(Benefit)
class BenefitAdmin(admin.ModelAdmin):
    list_display = ('name', 'benefit_type', 'provider', 'is_mandatory', 'is_active')
    list_filter = ('benefit_type', 'is_mandatory', 'is_active')
    search_fields = ('name', 'provider')

@admin.register(EmployeeBenefit)
class EmployeeBenefitAdmin(admin.ModelAdmin):
    list_display = ('employee', 'benefit', 'enrollment_date', 'status')
    list_filter = ('status', 'enrollment_date')
    search_fields = ('employee__first_name', 'benefit__name')
