from django.contrib import admin
from .models import Shift, ShiftAssignment

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('shift_name', 'start_time', 'end_time', 'working_hours', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('shift_name',)

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'shift', 'start_date', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('employee__first_name', 'shift__shift_name')
