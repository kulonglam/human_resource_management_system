from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='training_dashboard'),
    
    # Skills
    path('skills/', views.skill_list, name='skill_list'),
    path('skills/create/', views.skill_create, name='skill_create'),
    path('employee-skills/', views.employee_skill_list, name='employee_skill_list'),
    path('employee-skills/create/', views.employee_skill_create, name='employee_skill_create'),
    path('employee-skills/<int:pk>/edit/', views.employee_skill_edit, name='employee_skill_edit'),
    path('employee-skills/<int:pk>/delete/', views.employee_skill_delete, name='employee_skill_delete'),
    
    # Training Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    
    # Training Records
    path('training-records/', views.training_record_list, name='training_record_list'),
    path('training-records/create/', views.training_record_create, name='training_record_create'),
    path('training-records/<int:pk>/edit/', views.training_record_edit, name='training_record_edit'),
    
    # Certifications
    path('certifications/', views.certification_list, name='certification_list'),
    path('certifications/create/', views.certification_create, name='certification_create'),
    path('employee-certifications/', views.employee_certification_list, name='employee_certification_list'),
    path('employee-certifications/create/', views.employee_certification_create, name='employee_certification_create'),
    path('employee-certifications/<int:pk>/edit/', views.employee_certification_edit, name='employee_certification_edit'),
    
    # Development Plans
    path('development-plans/', views.development_plan_list, name='development_plan_list'),
    path('development-plans/create/', views.development_plan_create, name='development_plan_create'),
    path('development-plans/<int:pk>/', views.development_plan_detail, name='development_plan_detail'),
    path('development-plans/<int:pk>/edit/', views.development_plan_edit, name='development_plan_edit'),
]
