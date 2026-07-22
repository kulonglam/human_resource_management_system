"""Payroll domain HTTP adapters."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.audit import log_action
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.permissions import IsAdmin, IsPayrollManager, IsPayrollUser, RequiresMFAForPayroll
from api.serializers import PayrollRunSerializer, SalarySerializer
from payroll.models import PayrollRun, Salary
from payroll.utils import generate_salary_slip_pdf


class PayrollRunViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = PayrollRunSerializer

    def get_queryset(self):
        return self.scope_to_organization(PayrollRun.objects.all())

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsPayrollUser(), RequiresMFAForPayroll()]
        return [IsPayrollManager(), RequiresMFAForPayroll()]

    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id and not serializer.validated_data.get('organization'):
            kwargs['organization_id'] = org_id
        serializer.save(**kwargs)

    def update(self, request, *args, **kwargs):
        payroll_run = self.get_object()
        if payroll_run.status != 'draft':
            return Response(
                {'detail': 'Approved or paid payroll runs are locked.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        from payroll.services import approve_payroll_run

        payroll_run = self.get_object()
        try:
            payroll_run = approve_payroll_run(payroll_run, approved_by=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)
        log_action(request, 'approve', 'PayrollRun', payroll_run.id, str(payroll_run))
        return Response(PayrollRunSerializer(payroll_run).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def mark_paid(self, request, pk=None):
        from payroll.services import mark_payroll_run_paid

        payroll_run = self.get_object()
        try:
            payroll_run = mark_payroll_run_paid(payroll_run)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)
        log_action(request, 'update', 'PayrollRun', payroll_run.id, str(payroll_run), 'Payroll run paid.')
        return Response(PayrollRunSerializer(payroll_run).data)


class SalaryViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = SalarySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'slip'):
            return [IsAuthenticated(), RequiresMFAForPayroll()]
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsPayrollManager(), RequiresMFAForPayroll()]
        return [IsPayrollUser(), RequiresMFAForPayroll()]

    def get_queryset(self):
        qs = Salary.objects.select_related('employee').order_by('-year', '-month')
        qs = self.scope_to_accessible_employees(qs)
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month:
            qs = qs.filter(month=month)
        if year:
            qs = qs.filter(year=year)
        return qs

    def perform_create(self, serializer):
        from payroll.services import create_salary_in_run

        create_salary_in_run(serializer, created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        salary = self.get_object()
        if salary.status != 'draft':
            return Response(
                {'detail': 'Approved or paid payroll records are locked.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        salary = self.get_object()
        if salary.status != 'draft':
            return Response(
                {'detail': 'Approved or paid payroll records cannot be deleted.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def slip(self, request, pk=None):
        salary = self.get_object()
        return generate_salary_slip_pdf(salary)
