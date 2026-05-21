from django.contrib import admin
from .models import Leave, LeaveBalance


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('leave_type', 'status')
    search_fields = ('employee__user__first_name', 'employee__user__last_name')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_days', 'used_days', 'available_days')
    list_filter = ('year', 'leave_type')
    search_fields = ('employee__user__first_name', 'employee__user__last_name')
    readonly_fields = ('used_days', 'pending_days', 'available_days')

