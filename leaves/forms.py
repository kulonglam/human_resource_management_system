# leaves/forms.py
from django import forms

from attendance.models import Attendance
from .models import Leave  # adjust if your model name differs

class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = '__all__'  # or list specific fields, e.g. ['employee', 'date', 'status']