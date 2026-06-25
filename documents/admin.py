from django.contrib import admin

from .models import HRDocument


@admin.register(HRDocument)
class HRDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'employee', 'version', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
