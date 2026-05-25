from django.contrib import admin
from .models import Discipline, DisciplineAppeal

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('employee', 'discipline_type', 'incident_date', 'status')
    list_filter = ('discipline_type', 'status', 'incident_date')
    search_fields = ('employee__first_name', 'reason')
    ordering = ('-created_at',)

@admin.register(DisciplineAppeal)
class DisciplineAppealAdmin(admin.ModelAdmin):
    list_display = ('discipline', 'appeal_date', 'status')
    list_filter = ('status', 'appeal_date')
    search_fields = ('discipline__employee__first_name', 'appeal_reason')
