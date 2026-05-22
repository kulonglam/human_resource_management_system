from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Role, CustomUser, AuditLog


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role')
    list_filter = ('role',) + BaseUserAdmin.list_filter
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('get_action_display_custom', 'model_name', 'object_description', 'user', 'timestamp')
    list_filter = ('action', 'timestamp', 'model_name')
    search_fields = ('user__username', 'model_name', 'object_description', 'details')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_description', 'details', 'ip_address', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def get_action_display_custom(self, obj):
        return obj.get_action_display()
    get_action_display_custom.short_description = 'Action'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser