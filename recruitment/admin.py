from django.contrib import admin

from .models import Application, ApplicationNote, Interview, JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'deadline', 'is_open', 'posted_on')
    list_filter = ('department', 'is_open')
    search_fields = ('title', 'department')
    
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'job', 'status', 'source', 'rating', 'applied_on')
    list_filter = ('status', 'job', 'source')
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    list_display = ('application', 'author', 'created_at')
    search_fields = ('body',)


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'scheduled_at', 'status', 'interviewer_name')
    list_filter = ('status',)
