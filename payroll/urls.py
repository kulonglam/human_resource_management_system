from django.urls import path
from . import views



urlpatterns = [
   path('', views.salary_list, name='salary_list'),
   path('add/', views.salary_create, name='salary_create'),
   path('<int:pk>/edit/', views.salary_edit, name='salary_edit'),
   path('<int:pk>/slip/', views.salary_slip_pdf, name='salary_slip_pdf'),
]