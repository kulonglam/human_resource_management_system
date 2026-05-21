# kin/urls.py
from django.urls import path
from . import views



urlpatterns = [
    path('<int:employee_pk>/', views.kin_create_or_edit, name='kin_create_or_edit'),
]