from django.contrib import admin
from .models import Salary


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ('month', 'year', 'employee', 'net_salary', 'payment_method', 'is_paid')
    list_filter = ('month', 'year', 'payment_method', 'is_paid')
    search_fields = ('employee__first_name', 'employee__last_name')
   
