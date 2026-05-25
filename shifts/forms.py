from django import forms
from .models import Shift, ShiftAssignment

class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['shift_name', 'start_time', 'end_time', 'break_duration_minutes', 'working_hours', 'description']
        widgets = {
            'shift_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'break_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ShiftAssignmentForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ['employee', 'shift', 'department', 'start_date', 'end_date', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
