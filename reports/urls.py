from django.urls import path
from . import views

urlpatterns = [
    # Analytics Dashboard
    path('dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # Individual Reports
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('leave/', views.leave_report, name='leave_report'),
    path('payroll/', views.payroll_report, name='payroll_report'),
    path('performance/', views.performance_report, name='performance_report'),
    path('recruitment/', views.recruitment_report, name='recruitment_report'),
]
