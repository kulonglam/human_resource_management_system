"""Benefit enrollment HTTP adapters."""
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin
from api.permissions import IsAdminOrManagerOrReadOnly
from api.serializers import BenefitSerializer, EmployeeBenefitSerializer
from benefits.models import Benefit, EmployeeBenefit


class BenefitViewSet(AuditedModelViewSet):
    queryset = Benefit.objects.filter(is_active=True).order_by('name')
    serializer_class = BenefitSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeBenefitViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmployeeBenefitSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = EmployeeBenefit.objects.select_related('employee', 'benefit')
        qs = self.scope_to_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        from benefits.services import after_enrollment_created

        enrollment = serializer.save()
        after_enrollment_created(enrollment)

    def perform_update(self, serializer):
        from benefits.services import after_enrollment_updated

        previous_status = serializer.instance.status
        enrollment = serializer.save()
        after_enrollment_updated(enrollment, previous_status=previous_status)
