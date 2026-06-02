from django import forms
from avvento_hrmis.form_utils import BootstrapFormMixin
from .models import Salary


class SalaryForm(BootstrapFormMixin, forms.ModelForm):
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
