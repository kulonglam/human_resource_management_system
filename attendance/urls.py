from django.urls import path
from . import views



urlpatterns = [
   path('', views.attendance_list, name='attendance_list'),
   path('mark/', views.mark_attendance, name='mark_attendance'),
   path('report/', views.attendance_report, name='attendance_report'),
]