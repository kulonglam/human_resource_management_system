"""Exit process HTTP adapters."""
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin
from api.permissions import IsAdminOrManagerOrReadOnly
from api.serializers import ExitChecklistSerializer, ExitProcessSerializer
from exits.models import ExitChecklist, ExitProcess


class ExitProcessViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = ExitProcessSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ExitProcess.objects.select_related('employee').order_by('-created_at')
        return self.scope_to_accessible_employees(qs)


class ExitChecklistViewSet(AuditedModelViewSet):
    serializer_class = ExitChecklistSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ExitChecklist.objects.select_related('exit_process').order_by('exit_process', 'created_at')
        exit_id = self.request.query_params.get('exit_process')
        if exit_id:
            qs = qs.filter(exit_process_id=exit_id)
        return qs
