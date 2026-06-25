from django.contrib import admin

from .models import ApprovalDecision, ApprovalRequest, ApprovalStep, ApprovalWorkflow


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 1


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'workflow_type', 'is_default', 'is_active')
    list_filter = ('workflow_type', 'is_active')
    inlines = [ApprovalStepInline]


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'workflow', 'status', 'current_step_order', 'submitted_at')
    list_filter = ('status', 'workflow__workflow_type')


admin.site.register(ApprovalDecision)
