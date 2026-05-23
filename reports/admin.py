from django.contrib import admin
from .models import SavedReport, ReportSnapshot


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'created_by', 'created_at', 'is_public')
    list_filter = ('report_type', 'created_at', 'is_public')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ReportSnapshot)
class ReportSnapshotAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'generated_by', 'generated_at')
    list_filter = ('report_type', 'generated_at')
    search_fields = ('title', 'report_type')
    readonly_fields = ('generated_at',)
