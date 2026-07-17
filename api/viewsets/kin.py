"""Next-of-kin HTTP adapters."""
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin
from api.serializers import KinSerializer
from kin.models import Kin


class KinViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = KinSerializer

    def get_queryset(self):
        qs = Kin.objects.select_related('employee')
        qs = self.scope_to_accessible_employees(qs)
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs
