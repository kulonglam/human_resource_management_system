from django.contrib import admin
from .models import (
    PerformanceGoal, PerformanceAppraisal, FeedbackRound,
    FeedbackRequest, Feedback, FeedbackSummary
)


@admin.register(PerformanceGoal)
class PerformanceGoalAdmin(admin.ModelAdmin):
    list_display = ('goal_title', 'employee', 'status', 'priority', 'progress', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('goal_title', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Goal Information', {
            'fields': ('employee', 'goal_title', 'goal_description', 'target_metric')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Progress', {
            'fields': ('priority', 'status', 'progress', 'notes')
        }),
        ('Meta', {
            'fields': ('set_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(PerformanceAppraisal)
class PerformanceAppraisalAdmin(admin.ModelAdmin):
    list_display = ('employee', 'appraisal_period_start', 'appraisal_period_end', 'overall_rating', 'status')
    list_filter = ('status', 'appraisal_period_end')
    search_fields = ('employee__first_name', 'employee__last_name', 'appraiser__username')
    readonly_fields = ('overall_rating', 'created_at', 'submitted_at', 'reviewed_at', 'approved_at')
    fieldsets = (
        ('Appraisal Details', {
            'fields': ('employee', 'appraiser', 'appraisal_period_start', 'appraisal_period_end')
        }),
        ('Performance Ratings', {
            'fields': ('job_knowledge', 'work_quality', 'productivity', 'communication', 
                       'teamwork', 'initiative', 'reliability', 'overall_rating')
        }),
        ('Feedback', {
            'fields': ('strengths', 'areas_for_improvement', 'reviewer_comments')
        }),
        ('Development', {
            'fields': ('next_goals', 'training_needs')
        }),
        ('Status & Dates', {
            'fields': ('status', 'created_at', 'submitted_at', 'reviewed_at', 'approved_at')
        }),
    )


@admin.register(FeedbackRound)
class FeedbackRoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


@admin.register(FeedbackRequest)
class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'feedback_giver', 'giver_type', 'feedback_round', 'status', 'created_at')
    list_filter = ('status', 'giver_type', 'feedback_round', 'created_at')
    search_fields = ('recipient__first_name', 'recipient__last_name', 'feedback_giver__username')
    readonly_fields = ('created_at', 'submitted_at')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('request', 'communication', 'leadership', 'teamwork', 'is_anonymous', 'created_at')
    list_filter = ('is_anonymous', 'created_at')
    search_fields = ('request__recipient__first_name', 'request__recipient__last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Request', {
            'fields': ('request',)
        }),
        ('Competency Ratings', {
            'fields': ('communication', 'leadership', 'teamwork', 'reliability', 'initiative', 'problem_solving')
        }),
        ('Feedback', {
            'fields': ('strengths', 'areas_for_improvement', 'additional_comments', 'is_anonymous')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(FeedbackSummary)
class FeedbackSummaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'feedback_round', 'total_responses', 'created_at')
    list_filter = ('feedback_round', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name')
    readonly_fields = ('created_at',)
