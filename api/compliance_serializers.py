from rest_framework import serializers

from compliance.models import ComplianceEvidencePack, DataRetentionPolicy, VulnerabilityFinding


class DataRetentionPolicySerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = DataRetentionPolicy
        fields = [
            'id', 'category', 'category_label', 'retention_days', 'is_active',
            'description', 'last_run_at', 'last_purged_count', 'updated_at',
        ]
        read_only_fields = ['category', 'category_label', 'last_run_at', 'last_purged_count', 'updated_at']


class RetentionPreviewSerializer(serializers.Serializer):
    category = serializers.CharField()
    category_label = serializers.CharField()
    retention_days = serializers.IntegerField()
    eligible_count = serializers.IntegerField()


class ComplianceEvidencePackSerializer(serializers.ModelSerializer):
    control_label = serializers.CharField(source='get_control_display', read_only=True)

    class Meta:
        model = ComplianceEvidencePack
        fields = [
            'id', 'control', 'control_label', 'title', 'description', 'evidence_url',
            'owner', 'last_reviewed_at', 'next_review_at', 'status', 'updated_at',
        ]


class VulnerabilityFindingSerializer(serializers.ModelSerializer):
    sla_breached = serializers.BooleanField(read_only=True)

    class Meta:
        model = VulnerabilityFinding
        fields = [
            'id', 'title', 'severity', 'status', 'discovered_at', 'due_at',
            'resolved_at', 'description', 'remediation', 'sla_breached',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'sla_breached']
