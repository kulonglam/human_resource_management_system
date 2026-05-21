from django import forms
from .models import Kin

class KinForm(forms.ModelForm):
    class Meta:
        model = Kin
        exclude = ['employee']