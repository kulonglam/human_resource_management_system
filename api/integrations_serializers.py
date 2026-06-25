from rest_framework import serializers

from integrations.models import WEBHOOK_EVENTS, APIKey, WebhookDelivery, WebhookEndpoint


class APIKeySerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = APIKey
        fields = ['id', 'name', 'prefix', 'created_by', 'is_active', 'last_used_at', 'created_at']
        read_only_fields = fields


class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = ['id', 'name', 'url', 'events', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class WebhookDeliverySerializer(serializers.ModelSerializer):
    endpoint_name = serializers.CharField(source='endpoint.name', read_only=True)
    endpoint_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'endpoint_id', 'endpoint_name', 'event', 'success', 'status_code',
            'error_message', 'payload', 'delivered_at',
        ]
        read_only_fields = fields


class WebhookEventsSerializer(serializers.Serializer):
    events = serializers.ListField(child=serializers.CharField())

    def validate_events(self, value):
        invalid = [event for event in value if event not in WEBHOOK_EVENTS]
        if invalid:
            raise serializers.ValidationError(f'Invalid events: {", ".join(invalid)}')
        return value
