"""Reports domain serializers."""
from rest_framework import serializers

from reports.models import ReportSnapshot, SavedReport, ScheduledReport

class SavedReportSerializer(serializers.ModelSerializer):
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SavedReport
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'filters', 'is_public', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']



class ScheduledReportSerializer(serializers.ModelSerializer):
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ScheduledReport
        fields = [
            'id', 'name', 'report_type', 'report_type_display', 'filters',
            'frequency', 'frequency_display', 'export_format', 'recipient_emails',
            'is_active', 'last_run_at', 'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'last_run_at', 'created_at', 'updated_at']



class ReportSnapshotSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True, default=None)

    class Meta:
        model = ReportSnapshot
        fields = [
            'id', 'report_type', 'title', 'report_data', 'filters_used',
            'generated_by', 'generated_by_name', 'generated_at',
        ]
        read_only_fields = ['generated_by', 'generated_at']

