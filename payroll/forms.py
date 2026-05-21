# payroll/forms.py
from django import forms
from .models import Salary


class SalaryForm(forms.ModelForm):
    paid_on = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Salary
        fields = [
            'employee', 'month', 'year',
            'basic_salary', 'allowances', 'deductions', 'tax',
            'payment_frequency', 'payment_method',
            'paid_on', 'is_paid',
        ]
