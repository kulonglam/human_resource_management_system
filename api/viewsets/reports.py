"""Reports domain HTTP adapters."""
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.mixins import AuditedModelViewSet, OrganizationQuerysetMixin
from api.permissions import CanManageReports, IsAdminOrManager
from api.serializers import ReportSnapshotSerializer, SavedReportSerializer, ScheduledReportSerializer


class SavedReportViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = SavedReportSerializer

    def get_queryset(self):
        from reports.models import SavedReport

        user = self.request.user
        qs = SavedReport.objects.filter(
            Q(created_by=user) | Q(is_public=True),
        ).select_related('created_by').order_by('-updated_at')
        return self.scope_to_organization(qs)

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [CanManageReports()]

    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id and not serializer.validated_data.get('organization'):
            kwargs['organization_id'] = org_id
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Return saved filters for the SPA to load into the Reports page."""
        saved = self.get_object()
        return Response({
            'report_type': saved.report_type,
            'filters': saved.filters,
            'name': saved.name,
        })


class ReportSnapshotViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = ReportSnapshotSerializer

    def get_queryset(self):
        from reports.models import ReportSnapshot

        qs = ReportSnapshot.objects.select_related('generated_by').order_by('-generated_at')
        qs = self.scope_to_organization(qs)
        report_type = self.request.query_params.get('report_type')
        if report_type:
            qs = qs.filter(report_type=report_type)
        if not self.request.user.is_admin:
            qs = qs.filter(generated_by=self.request.user)
        return qs

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [CanManageReports()]

    def perform_create(self, serializer):
        kwargs = {'generated_by': self.request.user}
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id and not serializer.validated_data.get('organization'):
            kwargs['organization_id'] = org_id
        serializer.save(**kwargs)


class ScheduledReportViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = ScheduledReportSerializer

    def get_queryset(self):
        from reports.models import ScheduledReport

        return self.scope_to_organization(
            ScheduledReport.objects.select_related('created_by').order_by('name')
        )

    def get_permissions(self):
        return [CanManageReports()]

    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id and not serializer.validated_data.get('organization'):
            kwargs['organization_id'] = org_id
        serializer.save(**kwargs)

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        from reports.services import deliver_scheduled_report

        scheduled = self.get_object()
        try:
            result = deliver_scheduled_report(scheduled.id)
            return Response(result)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
