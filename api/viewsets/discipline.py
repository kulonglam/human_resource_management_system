"""Discipline HTTP adapters."""
from rest_framework.decorators import action
from rest_framework.response import Response

from api.audit import log_action
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin
from api.permissions import IsAdminOrManager, IsAdminOrManagerOrReadOnly
from api.serializers import DisciplineAppealSerializer, DisciplineSerializer
from discipline.models import Discipline, DisciplineAppeal


class DisciplineViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = DisciplineSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = Discipline.objects.select_related('employee').order_by('-created_at')
        qs = self.scope_to_accessible_employees(qs)
        return qs


class DisciplineAppealViewSet(AuditedModelViewSet):
    queryset = DisciplineAppeal.objects.all().order_by('-created_at')
    serializer_class = DisciplineAppealSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def perform_create(self, serializer):
        from discipline.services import after_appeal_created

        appeal = serializer.save()
        after_appeal_created(appeal)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        from discipline.services import approve_discipline_appeal

        appeal = self.get_object()
        approve_discipline_appeal(appeal, review_notes=request.data.get('review_notes', appeal.review_notes))
        log_action(
            request, 'approve', 'DisciplineAppeal', appeal.id, str(appeal),
            'Discipline appeal approved',
        )
        return Response(DisciplineAppealSerializer(appeal).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        from discipline.services import reject_discipline_appeal

        appeal = self.get_object()
        reject_discipline_appeal(appeal, review_notes=request.data.get('review_notes', appeal.review_notes))
        log_action(
            request, 'reject', 'DisciplineAppeal', appeal.id, str(appeal),
            'Discipline appeal rejected',
        )
        return Response(DisciplineAppealSerializer(appeal).data)
