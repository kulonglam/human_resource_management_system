"""Expense HTTP adapters."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from api.approval_integration import process_expense_decision
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.notifications import notify_expense_decision
from api.permissions import IsAdminOrManager, IsAdminOrManagerOrReadOnly
from api.serializers import ExpenseCategorySerializer, ExpenseSerializer
from expenses.models import Expense, ExpenseCategory


class ExpenseCategoryViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(ExpenseCategory.objects.filter(is_active=True).order_by('name'))


class ExpenseViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = ExpenseSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Expense.objects.select_related('employee', 'category').order_by('-created_at')
        qs = self.scope_to_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        from expenses.services import submit_expense

        expense = serializer.save()
        submit_expense(expense=expense, submitted_by=self.request.user)

    def perform_update(self, serializer):
        from expenses.services import submit_expense

        previous_status = serializer.instance.status
        expense = serializer.save()
        if previous_status != 'submitted' and expense.status == 'submitted':
            submit_expense(expense=expense, submitted_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        expense = self.get_object()
        outcome = process_expense_decision(request, expense, True, request.data.get('comment', ''))
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        expense.refresh_from_db()
        if outcome['result'] == 'approved':
            notify_expense_decision(expense, 'approved')
        elif outcome['result'] == 'rejected':
            notify_expense_decision(expense, 'rejected')
        return Response(ExpenseSerializer(expense, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        expense = self.get_object()
        outcome = process_expense_decision(
            request, expense, False, request.data.get('reason', request.data.get('comment', '')),
        )
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        expense.refresh_from_db()
        notify_expense_decision(expense, 'rejected')
        return Response(ExpenseSerializer(expense, context={'request': request}).data)
