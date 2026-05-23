from django import forms
from datetime import datetime, timedelta


class AttendanceReportForm(forms.Form):
    """Filter form for attendance reports."""
    DATE_RANGE_CHOICES = [
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Range'),
    ]
    
    date_range = forms.ChoiceField(choices=DATE_RANGE_CHOICES, initial='this_month', widget=forms.RadioSelect)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    attendance_status = forms.MultipleChoiceField(
        choices=[
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            ('on_leave', 'On Leave'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from departments.models import Department
        self.fields['department'].queryset = Department.objects.all()


class LeaveReportForm(forms.Form):
    """Filter form for leave reports."""
    REPORT_TYPE_CHOICES = [
        ('summary', 'Leave Summary'),
        ('detailed', 'Detailed Leave Report'),
        ('balance', 'Leave Balance Report'),
        ('pending', 'Pending Approvals'),
    ]
    
    report_type = forms.ChoiceField(choices=REPORT_TYPE_CHOICES, widget=forms.RadioSelect)
    
    year = forms.IntegerField(
        initial=datetime.now().year,
        widget=forms.Select(attrs={'class': 'form-select'}, choices=[(y, y) for y in range(2020, datetime.now().year + 1)])
    )
    
    leave_type = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.MultipleChoiceField(
        choices=[
            ('approved', 'Approved'),
            ('pending', 'Pending'),
            ('rejected', 'Rejected'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from departments.models import Department
        from leaves.models import Leave
        
        self.fields['department'].queryset = Department.objects.all()
        
        leave_types = Leave.objects.values_list('leave_type', 'leave_type').distinct()
        self.fields['leave_type'].choices = leave_types


class PayrollReportForm(forms.Form):
    """Filter form for payroll reports."""
    REPORT_TYPE_CHOICES = [
        ('summary', 'Payroll Summary'),
        ('detailed', 'Detailed Payroll Report'),
        ('deductions', 'Deductions Report'),
        ('tax', 'Tax Report'),
    ]
    
    report_type = forms.ChoiceField(choices=REPORT_TYPE_CHOICES, widget=forms.RadioSelect)
    
    month = forms.IntegerField(
        initial=datetime.now().month,
        widget=forms.Select(attrs={'class': 'form-select'}, choices=[(i, f"Month {i}") for i in range(1, 13)])
    )
    
    year = forms.IntegerField(
        initial=datetime.now().year,
        widget=forms.Select(attrs={'class': 'form-select'}, choices=[(y, y) for y in range(2020, datetime.now().year + 1)])
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    employee_status = forms.MultipleChoiceField(
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from departments.models import Department
        self.fields['department'].queryset = Department.objects.all()


class PerformanceReportForm(forms.Form):
    """Filter form for performance reports."""
    report_type = forms.ChoiceField(
        choices=[
            ('appraisal_summary', 'Appraisal Summary'),
            ('goal_progress', 'Goal Progress'),
            ('feedback_360', '360 Feedback Analysis'),
        ],
        widget=forms.RadioSelect
    )
    
    appraisal_period = forms.ChoiceField(
        choices=[
            ('current', 'Current Period'),
            ('previous', 'Previous Period'),
            ('all', 'All Periods'),
        ],
        widget=forms.RadioSelect
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    performance_rating = forms.MultipleChoiceField(
        choices=[
            (1, 'Needs Improvement'),
            (2, 'Below Average'),
            (3, 'Average'),
            (4, 'Good'),
            (5, 'Excellent'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from departments.models import Department
        self.fields['department'].queryset = Department.objects.all()


class RecruitmentReportForm(forms.Form):
    """Filter form for recruitment reports."""
    report_type = forms.ChoiceField(
        choices=[
            ('job_summary', 'Job Openings Summary'),
            ('applicant_status', 'Applicant Status'),
            ('hiring_funnel', 'Hiring Funnel'),
        ],
        widget=forms.RadioSelect
    )
    
    job_status = forms.MultipleChoiceField(
        choices=[
            ('open', 'Open'),
            ('closed', 'Closed'),
            ('filled', 'Filled'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from departments.models import Department
        self.fields['department'].queryset = Department.objects.all()


class HRAnalyticsForm(forms.Form):
    """Filter form for HR analytics dashboard."""
    time_period = forms.ChoiceField(
        choices=[
            ('this_month', 'This Month'),
            ('this_quarter', 'This Quarter'),
            ('this_year', 'This Year'),
            ('all_time', 'All Time'),
        ],
        widget=forms.RadioSelect
    )
    
    departments = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Leave blank for all departments"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from departments.models import Department
        self.fields['departments'].queryset = Department.objects.all()
