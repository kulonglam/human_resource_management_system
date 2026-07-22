"""Shift HTTP adapters."""
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.permissions import IsAdminOrManagerOrReadOnly
from api.serializers import ShiftAssignmentSerializer, ShiftSerializer
from shifts.models import Shift, ShiftAssignment


class ShiftViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = ShiftSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(Shift.objects.filter(is_active=True).order_by('start_time'))


class ShiftAssignmentViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = ShiftAssignmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ShiftAssignment.objects.select_related('employee', 'shift', 'department')
        qs = self.scope_to_accessible_employees(qs)
        return qs
