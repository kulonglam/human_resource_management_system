from django.urls import path
from . import views

 
urlpatterns = [
   path('', views.job_list, name='job_list'),
   path('<int:pk>/', views.job_detail, name='job_detail'),
   path('add/', views.job_create, name='job_create'),
   path('<int:pk>/edit/', views.job_edit, name='job_edit'),
   path('<int:job_pk>/applications/', views.application_list, name='application_list'),
   path('applications/<int:pk>/update/', views.application_update, name='application_update'),

]