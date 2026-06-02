# recruitment/forms.py
from django import forms
from avvento_hrmis.form_utils import BootstrapFormMixin
from .models import JobPosting, Application


class JobPostingForm(BootstrapFormMixin, forms.ModelForm):
    deadline = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = JobPosting
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
        }


class ApplicationStatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']
