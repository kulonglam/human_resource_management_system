"""Asset HTTP adapters."""
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.permissions import IsAdminOrManagerOrReadOnly
from api.serializers import AssetAssignmentSerializer, AssetSerializer
from assets.models import Asset, AssetAssignment


class AssetViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = AssetSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(Asset.objects.all().order_by('-created_at'))


class AssetAssignmentViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = AssetAssignment.objects.select_related('asset', 'employee').order_by('-assignment_date')
        qs = self.scope_to_accessible_employees(qs)
        return qs
