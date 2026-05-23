from django.contrib import admin
from .models import (
    Skill, EmployeeSkill, TrainingCourse, TrainingRecord,
    Certification, EmployeeCertification, DevelopmentPlan
)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmployeeSkill)
class EmployeeSkillAdmin(admin.ModelAdmin):
    list_display = ('employee', 'skill', 'proficiency_level', 'years_of_experience', 'verified')
    list_filter = ('proficiency_level', 'verified', 'skill__category')
    search_fields = ('employee__first_name', 'employee__last_name', 'skill__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'provider', 'start_date', 'end_date', 'status')
    list_filter = ('category', 'status', 'is_online', 'start_date')
    search_fields = ('title', 'provider', 'description')
    filter_horizontal = ('related_skills',)
    readonly_fields = ('created_at', 'updated_at', 'participants_count')


@admin.register(TrainingRecord)
class TrainingRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'course', 'status', 'score', 'certificate_issued')
    list_filter = ('status', 'certificate_issued', 'enrolled_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'course__title')
    readonly_fields = ('enrolled_date', 'updated_at')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'issuing_body', 'validity_years')
    search_fields = ('name', 'issuing_body')
    readonly_fields = ('created_at',)


@admin.register(EmployeeCertification)
class EmployeeCertificationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'certification', 'issue_date', 'expiry_date', 'status')
    list_filter = ('status', 'issue_date', 'expiry_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'certification__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DevelopmentPlan)
class DevelopmentPlanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'title', 'status', 'start_date', 'end_date', 'progress')
    list_filter = ('status', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'title')
    filter_horizontal = ('planned_courses', 'target_skills')
    readonly_fields = ('created_at', 'updated_at')
