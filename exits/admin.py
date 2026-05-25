from django.contrib import admin
from .models import ExitProcess, ExitChecklist

@admin.register(ExitProcess)
class ExitProcessAdmin(admin.ModelAdmin):
    list_display = ('employee', 'exit_date', 'reason', 'status')
    list_filter = ('status', 'reason', 'exit_date')
    search_fields = ('employee__first_name', 'employee__last_name')
    ordering = ('-created_at',)

@admin.register(ExitChecklist)
class ExitChecklistAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'exit_process', 'status', 'completion_date')
    list_filter = ('status', 'created_at')
    search_fields = ('item_name', 'exit_process__employee__first_name')
