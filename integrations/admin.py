from django.contrib import admin

from .models import APIKey, WebhookDelivery, WebhookEndpoint


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefix', 'user', 'is_active', 'last_used_at', 'created_at')
    list_filter = ('is_active',)


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'event', 'success', 'status_code', 'delivered_at')
    list_filter = ('success', 'event')
