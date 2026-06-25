from rest_framework import serializers

from compliance.models import DataRetentionPolicy


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
