from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, ExpenseApprovalForm, ExpenseCategoryForm

@login_required
def expense_list(request):
    user = request.user
    if user.is_staff:
        expenses = Expense.objects.all()
    else:
        expenses = Expense.objects.filter(employee=user.employee)
    return render(request, 'expenses/list.html', {'expenses': expenses})

@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    return render(request, 'expenses/detail.html', {'expense': expense})

@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.employee = request.user.employee
            expense.save()
            messages.success(request, 'Expense created successfully')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/form.html', {'form': form, 'title': 'Create Expense'})

@login_required
def expense_submit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.status = 'submitted'
        expense.submitted_date = timezone.now()
        expense.save()
        messages.success(request, 'Expense submitted for approval')
        return redirect('expense_list')
    return render(request, 'expenses/confirm_submit.html', {'expense': expense})

@login_required
def expense_approve(request, pk):
    if not request.user.is_staff:
        return redirect('expense_list')
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseApprovalForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.approved_by = request.user.employee
            expense.approved_date = timezone.now()
            expense.save()
            messages.success(request, 'Expense approved')
            return redirect('expense_list')
    else:
        form = ExpenseApprovalForm(instance=expense)
    return render(request, 'expenses/approve.html', {'form': form, 'expense': expense})

@login_required
def category_list(request):
    categories = ExpenseCategory.objects.filter(is_active=True)
    return render(request, 'expenses/categories.html', {'categories': categories})

from django.utils import timezone
