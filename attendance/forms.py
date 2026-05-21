# attendance/forms.py
from django import forms
from .models import Attendance  # adjust if your model name differs

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'  # or list specific fields, e.g. ['employee', 'date', 'status']