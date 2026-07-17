"""Payroll run / salary use-cases (application layer)."""

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from payroll.models import PayrollRun, Salary


def get_or_create_draft_run(*, month, year, created_by=None):
    """Return the draft payroll run for a period, or raise if the period is locked."""
    try:
        payroll_run, _ = PayrollRun.objects.select_for_update().get_or_create(
            month=month,
            year=year,
            defaults={'created_by': created_by},
        )
    except IntegrityError:
        payroll_run = PayrollRun.objects.select_for_update().get(month=month, year=year)
    if payroll_run.status != 'draft':
        raise serializers.ValidationError(
            {'payroll_run': 'The payroll run for this period is already locked.'},
        )
    return payroll_run


def create_salary_in_run(serializer, *, created_by=None):
    """Persist a salary row attached to the period's draft payroll run."""
    with transaction.atomic():
        month = serializer.validated_data['month']
        year = serializer.validated_data['year']
        payroll_run = get_or_create_draft_run(month=month, year=year, created_by=created_by)
        return serializer.save(payroll_run=payroll_run)


def _lock_payroll_run(payroll_run):
    return PayrollRun.objects.select_for_update().get(pk=payroll_run.pk)


def approve_payroll_run(payroll_run, *, approved_by):
    with transaction.atomic():
        payroll_run = _lock_payroll_run(payroll_run)
        if payroll_run.status != 'draft':
            raise ValueError('Only draft payroll runs can be approved.')
        if not payroll_run.salary_records.exists():
            raise ValueError('Add salary records before approving this run.')
        payroll_run.salary_records.update(status='approved', is_paid=False)
        payroll_run.status = 'approved'
        payroll_run.approved_by = approved_by
        payroll_run.approved_at = timezone.now()
        payroll_run.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        return payroll_run


def mark_payroll_run_paid(payroll_run):
    with transaction.atomic():
        payroll_run = _lock_payroll_run(payroll_run)
        if payroll_run.status != 'approved':
            raise ValueError('Only approved payroll runs can be marked paid.')
        paid_at = timezone.now()
        payroll_run.salary_records.update(
            status='paid', is_paid=True, paid_on=paid_at.date(), updated_at=paid_at,
        )
        payroll_run.status = 'paid'
        payroll_run.paid_at = paid_at
        payroll_run.save(update_fields=['status', 'paid_at', 'updated_at'])
        return payroll_run
