from django.contrib import admin
from .models import Asset, AssetAssignment

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_code', 'name', 'category', 'current_status', 'purchase_date')
    list_filter = ('current_status', 'category', 'created_at')
    search_fields = ('asset_code', 'name', 'serial_number')
    ordering = ('-created_at',)

@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ('asset', 'employee', 'assignment_date', 'status')
    list_filter = ('status', 'assignment_date')
    search_fields = ('asset__name', 'employee__first_name')
