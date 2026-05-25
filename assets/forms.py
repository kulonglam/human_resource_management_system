from django import forms
from .models import Asset, AssetAssignment

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_code', 'name', 'category', 'description', 'purchase_date', 'purchase_price', 'serial_number', 'warranty_expiry']
        widgets = {
            'asset_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'warranty_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class AssetAssignmentForm(forms.ModelForm):
    class Meta:
        model = AssetAssignment
        fields = ['asset', 'employee', 'assignment_notes', 'condition_on_assignment']
        widgets = {
            'asset': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'assignment_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'condition_on_assignment': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AssetReturnForm(forms.ModelForm):
    class Meta:
        model = AssetAssignment
        fields = ['return_date', 'condition_on_return']
        widgets = {
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'condition_on_return': forms.TextInput(attrs={'class': 'form-control'}),
        }
