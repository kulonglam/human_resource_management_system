from django.urls import path
from . import views

app_name = 'shifts'

urlpatterns = [
    path('', views.shift_list, name='list'),
    path('<int:pk>/', views.shift_detail, name='detail'),
    path('create/', views.shift_create, name='create'),
    path('<int:pk>/update/', views.shift_update, name='update'),
    path('assignments/', views.shift_assignment_list, name='assignments'),
    path('assign/', views.shift_assign, name='assign'),
    path('assignments/<int:pk>/update/', views.shift_assignment_update, name='assignment_update'),
]
