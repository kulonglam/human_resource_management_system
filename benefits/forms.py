from django import forms
from .models import Benefit, EmployeeBenefit
from departments.models import Department

class BenefitForm(forms.ModelForm):
    departments = forms.ModelMultipleChoiceField(queryset=Department.objects.all(), required=False, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = Benefit
        fields = ['name', 'benefit_type', 'description', 'provider', 'cost_per_employee', 'employer_contribution', 'employee_contribution', 'is_mandatory', 'applicable_to_all']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'benefit_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'provider': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_per_employee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'employer_contribution': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'employee_contribution': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'applicable_to_all': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EmployeeBenefitForm(forms.ModelForm):
    class Meta:
        model = EmployeeBenefit
        fields = ['employee', 'benefit', 'enrollment_date', 'plan_type', 'beneficiary_name', 'beneficiary_relationship', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'benefit': forms.Select(attrs={'class': 'form-select'}),
            'enrollment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'plan_type': forms.TextInput(attrs={'class': 'form-control'}),
            'beneficiary_name': forms.TextInput(attrs={'class': 'form-control'}),
            'beneficiary_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EmployeeBenefitTerminationForm(forms.ModelForm):
    class Meta:
        model = EmployeeBenefit
        fields = ['termination_date', 'status']
        widgets = {
            'termination_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
