from django.urls import path
from . import views

app_name = 'leave_policies'

urlpatterns = [
    path('', views.policy_list, name='list'),
    path('<int:pk>/', views.policy_detail, name='detail'),
    path('create/', views.policy_create, name='create'),
    path('<int:pk>/update/', views.policy_update, name='update'),
    path('allocations/', views.allocation_list, name='allocations'),
    path('allocations/create/', views.allocation_create, name='allocation_create'),
]
