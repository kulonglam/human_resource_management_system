from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, viewsets
from .payroll_views import PayrollExportView
from .compliance_views import (
    DataRetentionPolicyViewSet,
    GDPRDataExportView,
    GDPRErasureView,
    RetentionPreviewView,
    RetentionRunView,
)
from .careers_views import PublicApplyView, PublicJobDetailView, PublicJobListView
from .recruitment_views import RecruitmentSummaryView
from .recruitment_enterprise_views import (
    InterviewCalendarView,
    PublicOfferDetailView,
    PublicOfferSignView,
    RecruitmentEEOReportView,
)
from .sso_views import SSOCallbackView, SSOConfigView, SSOStartView
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
router.register('application-notes', viewsets.ApplicationNoteViewSet, basename='application-note')
router.register('interviews', viewsets.InterviewViewSet, basename='interview')
router.register('pipeline-stages', viewsets.JobPipelineStageViewSet, basename='pipeline-stage')
router.register('hiring-team', viewsets.HiringTeamMemberViewSet, basename='hiring-team')
router.register('scorecard-criteria', viewsets.ScorecardCriterionViewSet, basename='scorecard-criterion')
router.register('scorecards', viewsets.ApplicationScorecardViewSet, basename='scorecard')
router.register('offer-templates', viewsets.OfferTemplateViewSet, basename='offer-template')
router.register('offers', viewsets.JobOfferViewSet, basename='offer')
router.register('hire-onboarding', viewsets.HireOnboardingViewSet, basename='hire-onboarding')
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
router.register('audit-logs', viewsets.AuditLogViewSet, basename='audit-log')
router.register('notifications', viewsets.NotificationViewSet, basename='notification')
router.register('documents', viewsets.HRDocumentViewSet, basename='document')
router.register('approval-workflows', viewsets.ApprovalWorkflowViewSet, basename='approval-workflow')
router.register('approval-requests', viewsets.ApprovalRequestViewSet, basename='approval-request')
router.register('api-keys', viewsets.APIKeyViewSet, basename='api-key')
router.register('webhooks', viewsets.WebhookEndpointViewSet, basename='webhook')
router.register('compliance/retention-policies', DataRetentionPolicyViewSet, basename='retention-policy')
router.register('users', viewsets.UserViewSet, basename='user')

urlpatterns = [
    path('auth/csrf/', views.CsrfView.as_view(), name='api-csrf'),
    path('auth/config/', views.AuthConfigView.as_view(), name='api-auth-config'),
    path('auth/sso/config/', SSOConfigView.as_view(), name='api-sso-config'),
    path('auth/sso/<str:provider>/start/', SSOStartView.as_view(), name='api-sso-start'),
    path('auth/sso/<str:provider>/callback/', SSOCallbackView.as_view(), name='api-sso-callback'),
    path('auth/login/', views.LoginView.as_view(), name='api-login'),
    path('auth/mfa/verify/', views.MFAVerifyView.as_view(), name='api-mfa-verify'),
    path('auth/mfa/setup/', views.MFASetupView.as_view(), name='api-mfa-setup'),
    path('auth/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('auth/register/', views.RegisterView.as_view(), name='api-register'),
    path('auth/me/', views.CurrentUserView.as_view(), name='api-me'),
    path('roles/', views.RoleListView.as_view(), name='api-roles'),
    path('dashboard/', views.DashboardView.as_view(), name='api-dashboard'),
    path('recruitment/summary/', RecruitmentSummaryView.as_view(), name='api-recruitment-summary'),
    path('recruitment/eeo-report/', RecruitmentEEOReportView.as_view(), name='api-recruitment-eeo'),
    path('interviews/<int:interview_id>/calendar.ics', InterviewCalendarView.as_view(), name='api-interview-ics'),
    path('offers/<int:offer_id>/public/', PublicOfferDetailView.as_view(), name='api-offer-public'),
    path('offers/<int:offer_id>/sign/', PublicOfferSignView.as_view(), name='api-offer-sign'),
    path('careers/jobs/', PublicJobListView.as_view(), name='api-careers-jobs'),
    path('careers/jobs/<int:job_id>/', PublicJobDetailView.as_view(), name='api-careers-job-detail'),
    path('careers/jobs/<int:job_id>/apply/', PublicApplyView.as_view(), name='api-careers-apply'),
    path('health/', views.HealthCheckView.as_view(), name='api-health'),
    path('reports/analytics/', views.ReportsAnalyticsView.as_view(), name='api-reports-analytics'),
    path('reports/filters/', ReportFiltersView.as_view(), name='api-reports-filters'),
    path('reports/attendance/', AttendanceReportView.as_view(), name='api-reports-attendance'),
    path('reports/leave/', LeaveReportView.as_view(), name='api-reports-leave'),
    path('reports/payroll/', PayrollReportView.as_view(), name='api-reports-payroll'),
    path('reports/performance/', PerformanceReportView.as_view(), name='api-reports-performance'),
    path('reports/recruitment/', RecruitmentReportView.as_view(), name='api-reports-recruitment'),
    path('payroll/export/', PayrollExportView.as_view(), name='api-payroll-export'),
    path('compliance/data-export/me/', GDPRDataExportView.as_view(), name='api-gdpr-export-me'),
    path('compliance/data-export/employees/<int:employee_id>/', GDPRDataExportView.as_view(), name='api-gdpr-export-employee'),
    path('compliance/erasure/<int:employee_id>/', GDPRErasureView.as_view(), name='api-gdpr-erasure'),
    path('compliance/retention-policies/preview/', RetentionPreviewView.as_view(), name='api-retention-preview'),
    path('compliance/retention-policies/run/', RetentionRunView.as_view(), name='api-retention-run'),
    path('', include(router.urls)),
]
