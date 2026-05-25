from django.contrib import admin
from .models import Expense, ExpenseCategory

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('employee', 'category', 'amount', 'expense_date', 'status')
    list_filter = ('status', 'category', 'expense_date')
    search_fields = ('employee__first_name', 'description')
    ordering = ('-created_at',)

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'requires_receipt', 'max_amount_per_claim', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
