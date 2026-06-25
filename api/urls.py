from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, viewsets
from .report_views import (
    AttendanceReportView,
    LeaveReportView,
    PayrollReportView,
    PerformanceReportView,
    RecruitmentReportView,
    ReportFiltersView,
)

router = DefaultRouter()
router.register('employees', viewsets.EmployeeViewSet, basename='employee')
router.register('departments', viewsets.DepartmentViewSet, basename='department')
router.register('leaves', viewsets.LeaveViewSet, basename='leave')
router.register('leave-balances', viewsets.LeaveBalanceViewSet, basename='leave-balance')
router.register('attendance', viewsets.AttendanceViewSet, basename='attendance')
router.register('jobs', viewsets.JobPostingViewSet, basename='job')
router.register('applications', viewsets.ApplicationViewSet, basename='application')
router.register('salaries', viewsets.SalaryViewSet, basename='salary')
router.register('performance-goals', viewsets.PerformanceGoalViewSet, basename='performance-goal')
router.register('performance-appraisals', viewsets.PerformanceAppraisalViewSet, basename='performance-appraisal')
router.register('feedback-rounds', viewsets.FeedbackRoundViewSet, basename='feedback-round')
router.register('feedback-requests', viewsets.FeedbackRequestViewSet, basename='feedback-request')
router.register('feedback', viewsets.FeedbackViewSet, basename='feedback')
router.register('skills', viewsets.SkillViewSet, basename='skill')
router.register('employee-skills', viewsets.EmployeeSkillViewSet, basename='employee-skill')
router.register('training-courses', viewsets.TrainingCourseViewSet, basename='training-course')
router.register('training-records', viewsets.TrainingRecordViewSet, basename='training-record')
router.register('certifications', viewsets.CertificationViewSet, basename='certification')
router.register('employee-certifications', viewsets.EmployeeCertificationViewSet, basename='employee-certification')
router.register('development-plans', viewsets.DevelopmentPlanViewSet, basename='development-plan')
router.register('exit-processes', viewsets.ExitProcessViewSet, basename='exit-process')
router.register('exit-checklist-items', viewsets.ExitChecklistViewSet, basename='exit-checklist')
router.register('assets', viewsets.AssetViewSet, basename='asset')
router.register('asset-assignments', viewsets.AssetAssignmentViewSet, basename='asset-assignment')
router.register('shifts', viewsets.ShiftViewSet, basename='shift')
router.register('shift-assignments', viewsets.ShiftAssignmentViewSet, basename='shift-assignment')
router.register('expense-categories', viewsets.ExpenseCategoryViewSet, basename='expense-category')
router.register('expenses', viewsets.ExpenseViewSet, basename='expense')
router.register('benefits', viewsets.BenefitViewSet, basename='benefit')
router.register('employee-benefits', viewsets.EmployeeBenefitViewSet, basename='employee-benefit')
router.register('leave-policies', viewsets.LeavePolicyViewSet, basename='leave-policy')
router.register('leave-policy-allocations', viewsets.LeavePolicyAllocationViewSet, basename='leave-policy-allocation')
router.register('discipline-records', viewsets.DisciplineViewSet, basename='discipline')
router.register('discipline-appeals', viewsets.DisciplineAppealViewSet, basename='discipline-appeal')
router.register('kin', viewsets.KinViewSet, basename='kin')
router.register('surveys', viewsets.SurveyViewSet, basename='survey')
router.register('survey-questions', viewsets.SurveyQuestionViewSet, basename='survey-question')
router.register('survey-responses', viewsets.SurveyResponseViewSet, basename='survey-response')

urlpatterns = [
    path('auth/csrf/', views.CsrfView.as_view(), name='api-csrf'),
    path('auth/login/', views.LoginView.as_view(), name='api-login'),
    path('auth/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('auth/register/', views.RegisterView.as_view(), name='api-register'),
    path('auth/me/', views.CurrentUserView.as_view(), name='api-me'),
    path('roles/', views.RoleListView.as_view(), name='api-roles'),
    path('users/', views.UserListView.as_view(), name='api-users'),
    path('dashboard/', views.DashboardView.as_view(), name='api-dashboard'),
    path('reports/analytics/', views.ReportsAnalyticsView.as_view(), name='api-reports-analytics'),
    path('reports/filters/', ReportFiltersView.as_view(), name='api-reports-filters'),
    path('reports/attendance/', AttendanceReportView.as_view(), name='api-reports-attendance'),
    path('reports/leave/', LeaveReportView.as_view(), name='api-reports-leave'),
    path('reports/payroll/', PayrollReportView.as_view(), name='api-reports-payroll'),
    path('reports/performance/', PerformanceReportView.as_view(), name='api-reports-performance'),
    path('reports/recruitment/', RecruitmentReportView.as_view(), name='api-reports-recruitment'),
    path('', include(router.urls)),
]
