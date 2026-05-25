from django.contrib import admin
from .models import Survey, SurveyQuestion, SurveyResponse

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'survey_type', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'survey_type', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)

@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'survey', 'question_type', 'is_required')
    list_filter = ('question_type', 'is_required')
    search_fields = ('question_text', 'survey__title')

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'question', 'respondent', 'created_at')
    list_filter = ('created_at', 'survey')
    search_fields = ('respondent__first_name', 'survey__title')
