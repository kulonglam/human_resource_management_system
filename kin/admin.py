from django.contrib import admin
from .models import Kin


@admin.register(Kin)
class KinAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'employee', 'relationship', 'mobile')
    search_fields = ('employee__first_name', 'employee__last_name', 'name')
