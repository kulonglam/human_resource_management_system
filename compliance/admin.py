from django.contrib import admin

from .models import DataRetentionPolicy


@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ('category', 'retention_days', 'is_active', 'last_run_at', 'last_purged_count')
    list_filter = ('is_active',)
    readonly_fields = ('last_run_at', 'last_purged_count', 'updated_at')
