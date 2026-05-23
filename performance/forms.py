from django import forms
from .models import PerformanceGoal, PerformanceAppraisal, FeedbackRound, FeedbackRequest, Feedback


class PerformanceGoalForm(forms.ModelForm):
    class Meta:
        model = PerformanceGoal
        fields = ['employee', 'goal_title', 'goal_description', 'start_date', 'end_date', 
                  'target_metric', 'priority', 'status', 'progress', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'goal_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter goal title'}),
            'goal_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_metric': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Increase sales by 20%'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'progress': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PerformanceAppraisalForm(forms.ModelForm):
    class Meta:
        model = PerformanceAppraisal
        fields = ['employee', 'appraisal_period_start', 'appraisal_period_end', 'appraiser',
                  'job_knowledge', 'work_quality', 'productivity', 'communication', 
                  'teamwork', 'initiative', 'reliability', 'strengths', 'areas_for_improvement',
                  'reviewer_comments', 'next_goals', 'training_needs', 'status']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'appraisal_period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appraisal_period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appraiser': forms.Select(attrs={'class': 'form-control'}),
            'job_knowledge': forms.Select(attrs={'class': 'form-control'}),
            'work_quality': forms.Select(attrs={'class': 'form-control'}),
            'productivity': forms.Select(attrs={'class': 'form-control'}),
            'communication': forms.Select(attrs={'class': 'form-control'}),
            'teamwork': forms.Select(attrs={'class': 'form-control'}),
            'initiative': forms.Select(attrs={'class': 'form-control'}),
            'reliability': forms.Select(attrs={'class': 'form-control'}),
            'strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'areas_for_improvement': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reviewer_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'next_goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'training_needs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class FeedbackRoundForm(forms.ModelForm):
    class Meta:
        model = FeedbackRound
        fields = ['name', 'description', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Q2 2024 360 Feedback'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['communication', 'leadership', 'teamwork', 'reliability', 'initiative',
                  'problem_solving', 'strengths', 'areas_for_improvement', 'additional_comments',
                  'is_anonymous']
        widgets = {
            'communication': forms.Select(attrs={'class': 'form-control'}),
            'leadership': forms.Select(attrs={'class': 'form-control'}),
            'teamwork': forms.Select(attrs={'class': 'form-control'}),
            'reliability': forms.Select(attrs={'class': 'form-control'}),
            'initiative': forms.Select(attrs={'class': 'form-control'}),
            'problem_solving': forms.Select(attrs={'class': 'form-control'}),
            'strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are this person\'s strengths?'}),
            'areas_for_improvement': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Areas for development'}),
            'additional_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
