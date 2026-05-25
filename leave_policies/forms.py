from django import forms
from .models import LeavePolicy, LeavePolicyAllocation
from departments.models import Department

class LeavePolicyForm(forms.ModelForm):
    departments = forms.ModelMultipleChoiceField(queryset=Department.objects.all(), required=False, widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = LeavePolicy
        fields = ['name', 'leave_type', 'days_per_year', 'carryforward_allowed', 'carryforward_limit', 'description', 'applicable_to_all']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'days_per_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'carryforward_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'carryforward_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'applicable_to_all': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class LeavePolicyAllocationForm(forms.ModelForm):
    class Meta:
        model = LeavePolicyAllocation
        fields = ['employee', 'policy', 'allocation_year', 'allocated_days', 'carryforward_days', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'policy': forms.Select(attrs={'class': 'form-select'}),
            'allocation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'allocated_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'carryforward_days': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
