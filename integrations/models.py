import hashlib
import hmac
import json
import logging
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import CustomUser
from accounts.tenancy import organization_fk

logger = logging.getLogger(__name__)

WEBHOOK_EVENTS = [
    'leave.submitted',
    'leave.approved',
    'leave.rejected',
    'employee.created',
    'employee.terminated',
    'expense.approved',
    'expense.rejected',
]


class APIKey(models.Model):
    SCOPE_CHOICES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('payroll', 'Payroll'),
        ('scim', 'SCIM provisioning'),
        ('export', 'Exports'),
        ('admin', 'Full admin'),
    ]

    name = models.CharField(max_length=100)
    prefix = models.CharField(max_length=12, unique=True, editable=False)
    key_hash = models.CharField(max_length=64, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='api_keys')
    organization = organization_fk(related_name='api_keys')
    scopes = models.JSONField(default=list, blank=True, help_text='Capability scopes for this key')
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.prefix}…)'

    def has_scope(self, scope):
        scopes = self.scopes or []
        return 'admin' in scopes or scope in scopes

    @classmethod
    def generate(cls, user, name, scopes=None):
        raw_key = secrets.token_urlsafe(32)
        prefix = raw_key[:8]
        key_hash = cls.hash_key(raw_key)
        instance = cls.objects.create(
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            user=user,
            organization_id=getattr(user, 'organization_id', None),
            scopes=scopes or ['read'],
        )
        return instance, raw_key

    @staticmethod
    def hash_key(raw_key):
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def authenticate(cls, raw_key):
        if not raw_key or len(raw_key) < 12:
            return None
        prefix = raw_key[:8]
        key_hash = cls.hash_key(raw_key)
        try:
            api_key = cls.objects.select_related('user').get(prefix=prefix, key_hash=key_hash, is_active=True)
        except cls.DoesNotExist:
            return None
        APIKey.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())
        return api_key


class WebhookEndpoint(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    events = models.JSONField(default=list, help_text='List of event names to subscribe to')
    secret = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    organization = organization_fk(related_name='webhook_endpoints')
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='webhooks',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = secrets.token_urlsafe(24)
        super().save(*args, **kwargs)


class WebhookDelivery(models.Model):
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='deliveries')
    event = models.CharField(max_length=50)
    payload = models.JSONField()
    status_code = models.PositiveIntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    attempt_count = models.PositiveSmallIntegerField(default=1)
    error_message = models.TextField(blank=True)
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-delivered_at']
        verbose_name_plural = 'Webhook deliveries'
