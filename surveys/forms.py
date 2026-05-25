from django import forms
from .models import Survey, SurveyQuestion, SurveyResponse

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description', 'survey_type', 'start_date', 'end_date', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'survey_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SurveyQuestionForm(forms.ModelForm):
    class Meta:
        model = SurveyQuestion
        fields = ['question_text', 'question_type', 'options', 'is_required', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'options': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Separate options with commas'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SurveyResponseForm(forms.ModelForm):
    class Meta:
        model = SurveyResponse
        fields = ['response_text', 'response_rating', 'response_selected']
        widgets = {
            'response_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'response_rating': forms.RadioSelect(),
            'response_selected': forms.CheckboxSelectMultiple(),
        }
