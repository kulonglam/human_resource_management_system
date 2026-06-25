from datetime import timedelta

from django.utils import timezone

from accounts.models import AuditLog, Notification
from integrations.models import WebhookDelivery
from recruitment.models import Application

from .models import DataRetentionPolicy


def _cutoff(days):
    return timezone.now() - timedelta(days=days)


def _queryset_for_category(category, cutoff):
    if category == 'audit_logs':
        return AuditLog.objects.filter(timestamp__lt=cutoff)
    if category == 'webhook_deliveries':
        return WebhookDelivery.objects.filter(delivered_at__lt=cutoff)
    if category == 'notifications':
        return Notification.objects.filter(created_at__lt=cutoff)
    if category == 'rejected_applications':
        return Application.objects.filter(status='rejected', applied_on__lt=cutoff)
    raise ValueError(f'Unknown retention category: {category}')


def preview_retention(policy):
    cutoff = _cutoff(policy.retention_days)
    return _queryset_for_category(policy.category, cutoff).count()


def apply_retention_policy(policy, dry_run=False):
    if not policy.is_active:
        return 0

    cutoff = _cutoff(policy.retention_days)
    qs = _queryset_for_category(policy.category, cutoff)
    count = qs.count()
    if count and not dry_run:
        qs.delete()
        policy.last_run_at = timezone.now()
        policy.last_purged_count = count
        policy.save(update_fields=['last_run_at', 'last_purged_count'])
    return count


def apply_all_retention_policies(dry_run=False):
    results = []
    for policy in DataRetentionPolicy.objects.filter(is_active=True):
        count = apply_retention_policy(policy, dry_run=dry_run)
        results.append({'category': policy.category, 'purged': count})
    return results
