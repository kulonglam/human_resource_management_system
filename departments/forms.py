from django import forms
from avvento_hrmis.form_utils import BootstrapFormMixin
from .models import Department

class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'
        widgets = {
            'history': forms.Textarea(attrs={'rows': 4}),
        }
