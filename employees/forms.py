from django import forms
from avvento_hrmis.form_utils import BootstrapFormMixin
from .models import Employee

class EmployeeForm(BootstrapFormMixin, forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    date_joined = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Employee
        fields = '__all__'
