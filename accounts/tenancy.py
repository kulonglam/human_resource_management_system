"""Shared organization tenancy helpers for models and querysets."""

from django.db import models


def organization_fk(*, related_name):
    """Nullable FK to Organization for multi-tenant catalog rows."""
    return models.ForeignKey(
        'accounts.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=related_name,
    )


def filter_queryset_for_organization(queryset, user, *, org_field='organization_id'):
    """
    Restrict a queryset to the caller's organization when set.

    Users without an organization (typical single-tenant admins) see all rows.
    """
    org_id = getattr(user, 'organization_id', None)
    if not org_id:
        return queryset
    return queryset.filter(**{org_field: org_id})


def assign_organization(instance, user, *, field='organization_id'):
    """Stamp creating user's organization when the instance has none."""
    org_id = getattr(user, 'organization_id', None)
    if org_id and not getattr(instance, field, None):
        setattr(instance, field, org_id)
        return True
    return False
