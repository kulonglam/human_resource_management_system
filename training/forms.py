from django import forms
from .models import (
    Skill, EmployeeSkill, TrainingCourse, TrainingRecord, 
    Certification, EmployeeCertification, DevelopmentPlan
)


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EmployeeSkillForm(forms.ModelForm):
    class Meta:
        model = EmployeeSkill
        fields = ['employee', 'skill', 'proficiency_level', 'years_of_experience', 'acquired_date', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'skill': forms.Select(attrs={'class': 'form-control'}),
            'proficiency_level': forms.Select(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.1}),
            'acquired_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['title', 'description', 'category', 'provider', 'duration_hours', 
                  'start_date', 'end_date', 'location', 'is_online', 'max_participants', 
                  'cost', 'status', 'related_skills', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'provider': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'related_skills': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class TrainingRecordForm(forms.ModelForm):
    class Meta:
        model = TrainingRecord
        fields = ['employee', 'course', 'status', 'completion_date', 'score', 'feedback', 'certificate_issued']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'certificate_issued': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'issuing_body', 'description', 'validity_years', 'required_for_roles']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'issuing_body': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'validity_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_for_roles': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated roles'}),
        }


class EmployeeCertificationForm(forms.ModelForm):
    class Meta:
        model = EmployeeCertification
        fields = ['employee', 'certification', 'issue_date', 'expiry_date', 'certificate_number', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'certification': forms.Select(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DevelopmentPlanForm(forms.ModelForm):
    class Meta:
        model = DevelopmentPlan
        fields = ['employee', 'title', 'description', 'goals', 'start_date', 'end_date', 
                  'status', 'progress', 'planned_courses', 'target_skills', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'progress': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'planned_courses': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
            'target_skills': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
