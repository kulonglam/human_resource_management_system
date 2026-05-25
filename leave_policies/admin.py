from django.contrib import admin
from .models import LeavePolicy, LeavePolicyAllocation

@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'leave_type', 'days_per_year', 'carryforward_allowed', 'is_active')
    list_filter = ('leave_type', 'is_active')
    search_fields = ('name',)

@admin.register(LeavePolicyAllocation)
class LeavePolicyAllocationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'policy', 'allocation_year', 'allocated_days', 'used_days')
    list_filter = ('allocation_year', 'policy')
    search_fields = ('employee__first_name', 'policy__name')
