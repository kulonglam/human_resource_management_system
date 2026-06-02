from django import forms
from avvento_hrmis.form_utils import BootstrapFormMixin
from .models import Kin

class KinForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Kin
        exclude = ['employee']
