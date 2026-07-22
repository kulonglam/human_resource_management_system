"""Leaves domain HTTP adapters."""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.approval_integration import process_leave_decision
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.notifications import notify_leave_decision
from api.permissions import IsAdmin, IsAdminOrManager, IsAdminOrManagerOrReadOnly
from api.serializers import (
    LeaveBalanceSerializer,
    LeavePolicyAllocationSerializer,
    LeavePolicySerializer,
    LeaveSerializer,
)
from employees.models import Employee
from leave_policies.models import LeavePolicy, LeavePolicyAllocation
from leaves.models import Leave, LeaveBalance


class LeaveViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = LeaveSerializer

    def get_queryset(self):
        qs = Leave.objects.select_related('employee').order_by('-applied_on')
        qs = self.scope_to_accessible_employees(qs)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        from leaves.services import submit_leave

        balance = serializer.validated_data.get('_leave_balance')
        leave = serializer.save()
        submit_leave(leave=leave, balance=balance, submitted_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'detail': 'Leave is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        outcome = process_leave_decision(request, leave, True, request.data.get('comment', ''))
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        leave.refresh_from_db()
        if outcome['result'] == 'approved':
            notify_leave_decision(leave, 'approved')
        elif outcome['result'] == 'rejected':
            notify_leave_decision(leave, 'rejected')
        return Response(LeaveSerializer(leave, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'detail': 'Leave is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        outcome = process_leave_decision(
            request, leave, False, request.data.get('reason', request.data.get('comment', '')),
        )
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        leave.refresh_from_db()
        notify_leave_decision(leave, 'rejected')
        return Response(LeaveSerializer(leave, context={'request': request}).data)


class LeaveBalanceViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = LeaveBalance.objects.select_related('employee').order_by('-year', 'leave_type')
        year = self.request.query_params.get('year')
        if year:
            qs = qs.filter(year=year)
        qs = self.scope_to_accessible_employees(qs)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrManager])
    def accrue(self, request):
        from leaves.services import accrue_monthly_balances

        result = accrue_monthly_balances(request.data.get('year'), request.data.get('month'))
        return Response(result)

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def carry_forward(self, request):
        from leaves.services import carry_forward_balances

        from_year = int(request.data.get('from_year', timezone.now().year - 1))
        to_year = int(request.data.get('to_year', timezone.now().year))
        return Response(carry_forward_balances(from_year, to_year))


class LeavePolicyViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(LeavePolicy.objects.filter(is_active=True).order_by('name'))


class LeavePolicyAllocationViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = LeavePolicyAllocationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = LeavePolicyAllocation.objects.select_related('employee', 'policy')
        qs = self.scope_to_accessible_employees(qs)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrManager])
    def sync(self, request):
        from leave_policies.services import sync_all_employees, sync_employee_allocations

        employee_id = request.data.get('employee')
        year = request.data.get('year')
        if employee_id:
            employee = Employee.objects.get(pk=employee_id)
            results = sync_employee_allocations(employee, year)
            return Response({'employee': employee.id, 'synced': len(results), 'details': results})
        summary = sync_all_employees(year)
        return Response(summary)
