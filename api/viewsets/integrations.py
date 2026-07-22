"""Integrations domain HTTP adapters."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.tenancy import filter_queryset_for_organization
from api.mixins import AuditedModelViewSet, OrganizationQuerysetMixin
from api.permissions import IsAdmin


class APIKeyViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        return [IsAdmin()]

    def get_serializer_class(self):
        from api.integrations_serializers import APIKeyCreateSerializer, APIKeySerializer
        if self.action == 'create':
            return APIKeyCreateSerializer
        return APIKeySerializer

    def get_queryset(self):
        from integrations.models import APIKey
        qs = APIKey.objects.select_related('user').order_by('-created_at')
        return filter_queryset_for_organization(qs, self.request.user)

    def create(self, request, *args, **kwargs):
        from integrations.models import APIKey
        from api.integrations_serializers import APIKeyCreateSerializer, APIKeySerializer

        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance, raw_key = APIKey.generate(
            request.user,
            serializer.validated_data['name'],
            scopes=serializer.validated_data.get('scopes') or ['read'],
        )
        data = APIKeySerializer(instance).data
        data['api_key'] = raw_key
        return Response(data, status=status.HTTP_201_CREATED)


class WebhookEndpointViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    def get_serializer_class(self):
        from api.integrations_serializers import WebhookDeliverySerializer, WebhookEndpointSerializer
        if self.action == 'deliveries':
            return WebhookDeliverySerializer
        return WebhookEndpointSerializer

    def get_queryset(self):
        from integrations.models import WebhookEndpoint
        return self.scope_to_organization(WebhookEndpoint.objects.order_by('name'))

    def get_permissions(self):
        return [IsAdmin()]

    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id and not serializer.validated_data.get('organization'):
            kwargs['organization_id'] = org_id
        serializer.save(**kwargs)

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        endpoint = self.get_object()
        from integrations.models import WebhookDelivery
        qs = WebhookDelivery.objects.filter(endpoint=endpoint).order_by('-delivered_at')[:50]
        from api.integrations_serializers import WebhookDeliverySerializer
        return Response(WebhookDeliverySerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='delivery-log')
    def delivery_log(self, request):
        from integrations.models import WebhookDelivery
        qs = WebhookDelivery.objects.select_related('endpoint').order_by('-delivered_at')
        endpoint_id = request.query_params.get('endpoint')
        if endpoint_id:
            qs = qs.filter(endpoint_id=endpoint_id)
        success = request.query_params.get('success')
        if success in ('1', 'true'):
            qs = qs.filter(success=True)
        elif success in ('0', 'false'):
            qs = qs.filter(success=False)
        limit = min(int(request.query_params.get('limit', 100)), 200)
        from api.integrations_serializers import WebhookDeliverySerializer
        return Response(WebhookDeliverySerializer(qs[:limit], many=True).data)

    @action(detail=False, methods=['post'], url_path='retry-delivery')
    def retry_delivery(self, request):
        from integrations.services import retry_webhook_delivery
        from api.integrations_serializers import WebhookDeliverySerializer

        delivery_id = request.data.get('delivery_id')
        if not delivery_id:
            return Response({'detail': 'delivery_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            delivery = retry_webhook_delivery(delivery_id)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(WebhookDeliverySerializer(delivery).data)

    @action(detail=False, methods=['get'])
    def events(self, request):
        from integrations.models import WEBHOOK_EVENTS
        return Response({'events': WEBHOOK_EVENTS})
