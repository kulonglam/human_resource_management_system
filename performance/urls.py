from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='performance_dashboard'),
    
    # Performance Goals
    path('goals/', views.goal_list, name='goal_list'),
    path('goals/create/', views.goal_create, name='goal_create'),
    path('goals/<int:pk>/', views.goal_detail, name='goal_detail'),
    path('goals/<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('goals/<int:pk>/delete/', views.goal_delete, name='goal_delete'),
    
    # Performance Appraisals
    path('appraisals/', views.appraisal_list, name='appraisal_list'),
    path('appraisals/create/', views.appraisal_create, name='appraisal_create'),
    path('appraisals/<int:pk>/', views.appraisal_detail, name='appraisal_detail'),
    path('appraisals/<int:pk>/edit/', views.appraisal_edit, name='appraisal_edit'),
    path('appraisals/<int:pk>/submit/', views.appraisal_submit, name='appraisal_submit'),
    path('appraisals/<int:pk>/approve/', views.appraisal_approve, name='appraisal_approve'),
    
    # 360 Feedback - Rounds
    path('feedback/rounds/', views.feedback_round_list, name='feedback_round_list'),
    path('feedback/rounds/create/', views.feedback_round_create, name='feedback_round_create'),
    path('feedback/rounds/<int:pk>/', views.feedback_round_detail, name='feedback_round_detail'),
    
    # 360 Feedback - Requests
    path('feedback/rounds/<int:round_id>/requests/create/', views.feedback_request_create, name='feedback_request_create'),
    path('feedback/my-requests/', views.my_feedback_requests, name='my_feedback_requests'),
    path('feedback/requests/<int:request_id>/submit/', views.feedback_submit, name='feedback_submit'),
    
    # 360 Feedback - Summary
    path('feedback/employee/<int:employee_id>/summary/', views.feedback_summary_view, name='feedback_summary'),
]
