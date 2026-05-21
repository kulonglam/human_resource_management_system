from django.contrib import admin

from .models import JobPosting, Application


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'deadline', 'is_open', 'posted_on')
    list_filter = ('department', 'is_open')
    search_fields = ('title', 'department')
    
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'job', 'status', 'applied_on')
    list_filter = ('status', 'job')
    search_fields = ('first_name', 'last_name', 'email')
