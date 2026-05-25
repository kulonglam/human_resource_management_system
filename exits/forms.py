from django import forms
from .models import ExitProcess, ExitChecklist

class ExitProcessForm(forms.ModelForm):
    class Meta:
        model = ExitProcess
        fields = ['exit_date', 'reason', 'notice_period_days', 'last_working_day', 'notes']
        widgets = {
            'exit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'notice_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'last_working_day': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ExitChecklistForm(forms.ModelForm):
    class Meta:
        model = ExitChecklist
        fields = ['item_name', 'responsible_person', 'notes']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible_person': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ExitChecklistStatusForm(forms.ModelForm):
    class Meta:
        model = ExitChecklist
        fields = ['status', 'completion_date', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
