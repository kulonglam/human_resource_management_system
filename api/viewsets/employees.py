"""Employees domain HTTP adapters."""
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.access_control import can_access_employee, get_user_accessible_employees
from api.audit import log_action
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.permissions import IsAdminOrManagerOrReadOnly
from api.serializers import (
    DepartmentSerializer,
    EmployeeSerializer,
    EmployeeTerminateSerializer,
    EmploymentContractSerializer,
    EmploymentHistorySerializer,
    JobGradeSerializer,
    PositionSerializer,
)
from departments.models import Department
from employees.models import Employee, EmploymentContract, EmploymentHistory, JobGrade, Position


class EmployeeViewSet(AuditedModelViewSet):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        qs = get_user_accessible_employees(self.request.user).filter(is_active=True).order_by(
            'last_name', 'first_name', 'id',
        )
        query = self.request.query_params.get('q', '').strip()
        if query:
            qs = qs.filter(
                Q(employee_number__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(job_title__icontains=query)
                | Q(department__name__icontains=query)
            )
        return qs.select_related('department')

    def retrieve(self, request, *args, **kwargs):
        employee = self.get_object()
        if not can_access_employee(request.user, employee):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        from accounts.access_control import can_view_sensitive_data
        from api.sensitive_access import log_sensitive_employee_access

        if can_view_sensitive_data(request.user):
            log_sensitive_employee_access(request, employee)
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        employee = self.get_object()
        if not can_access_employee(request.user, employee):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Use terminate action instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        if not request.user.is_admin:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        employee = self.get_object()
        serializer = EmployeeTerminateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from employees.services import terminate_employee

        terminate_employee(
            employee,
            exit_reason=serializer.validated_data['exit_reason'],
            exit_notes=serializer.validated_data.get('exit_notes', ''),
            actor=request.user,
        )
        log_action(
            request, 'update', 'Employee', employee.id, employee.full_name,
            f'Employee terminated: {employee.exit_reason}',
        )
        return Response(EmployeeSerializer(employee, context={'request': request}).data)

    def perform_create(self, serializer):
        from employees.services import after_employee_created, assign_organization_if_needed

        employee = serializer.save()
        assign_organization_if_needed(employee, self.request.user)
        after_employee_created(employee)


class JobGradeViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = JobGradeSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(JobGrade.objects.all())


class PositionViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(
            Position.objects.select_related('department', 'grade', 'reports_to').all()
        )


class EmploymentContractViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmploymentContractSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = EmploymentContract.objects.select_related('employee').all()
        return self.scope_to_accessible_employees(qs)


class EmploymentHistoryViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmploymentHistorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = EmploymentHistory.objects.select_related('employee').all()
        return self.scope_to_accessible_employees(qs)

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class DepartmentViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(Department.objects.select_related('parent').all())

    @action(detail=False, methods=['get'])
    def org_chart(self, request):
        from departments.services import build_org_chart
        return Response(build_org_chart(organization_id=getattr(request.user, 'organization_id', None)))
