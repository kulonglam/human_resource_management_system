from django import forms
from .models import Discipline, DisciplineAppeal

class DisciplineForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ['employee', 'discipline_type', 'reason', 'detailed_reason', 'incident_date', 'next_review_date', 'documents', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'discipline_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'detailed_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'incident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_review_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'documents': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DisciplineStatusForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DisciplineAppealForm(forms.ModelForm):
    class Meta:
        model = DisciplineAppeal
        fields = ['appeal_date', 'appeal_reason', 'supporting_documents']
        widgets = {
            'appeal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appeal_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'supporting_documents': forms.FileInput(attrs={'class': 'form-control'}),
        }

class DisciplineAppealReviewForm(forms.ModelForm):
    class Meta:
        model = DisciplineAppeal
        fields = ['status', 'review_date', 'review_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'review_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'review_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
