"""Expense submission use-cases (application layer)."""

from django.db import transaction

from expenses.models import Expense


def submit_expense(*, expense, submitted_by):
    """Notify and start approval workflow when an expense is submitted."""
    from api.approval_integration import start_expense_approval
    from api.notifications import notify_expense_submitted

    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.status in ('submitted', 'approved'):
            notify_expense_submitted(expense)
            start_expense_approval(expense, submitted_by)
    return expense


def finalize_expense_approval(*, expense):
    """Mark expense approved under row lock (idempotent if already approved)."""
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.status == 'approved':
            return expense
        if expense.status == 'rejected':
            raise ValueError('Rejected expenses cannot be approved.')
        if expense.status == 'paid':
            raise ValueError('Paid expenses cannot be re-approved.')
        from django.utils import timezone
        expense.status = 'approved'
        expense.approved_date = timezone.now()
        expense.save(update_fields=['status', 'approved_date', 'updated_at'])
    return expense


def reject_expense(*, expense, reason=''):
    """Mark expense rejected under row lock."""
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.status == 'rejected':
            return expense
        if expense.status in ('approved', 'paid'):
            raise ValueError('Approved or paid expenses cannot be rejected.')
        expense.status = 'rejected'
        expense.rejection_reason = reason
        expense.save(update_fields=['status', 'rejection_reason', 'updated_at'])
    return expense
