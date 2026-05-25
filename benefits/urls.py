from django.urls import path
from . import views

app_name = 'benefits'

urlpatterns = [
    path('', views.benefit_list, name='list'),
    path('<int:pk>/', views.benefit_detail, name='detail'),
    path('create/', views.benefit_create, name='create'),
    path('<int:pk>/update/', views.benefit_update, name='update'),
    path('enrollments/', views.enrollment_list, name='enrollments'),
    path('enroll/', views.enrollment_create, name='enroll'),
    path('enrollments/<int:pk>/terminate/', views.enrollment_terminate, name='terminate'),
]
