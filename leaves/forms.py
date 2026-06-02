from django import forms
from django.contrib.auth import get_user_model
from attendance.models import Attendance
from avvento_hrmis.form_utils import BootstrapFormMixin
from .models import Leave
from employees.models import Employee

User = get_user_model()

class LeaveForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
