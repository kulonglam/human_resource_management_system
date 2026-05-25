from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.asset_list, name='list'),
    path('<int:pk>/', views.asset_detail, name='detail'),
    path('create/', views.asset_create, name='create'),
    path('<int:pk>/update/', views.asset_update, name='update'),
    path('assign/', views.asset_assign, name='assign'),
    path('assignments/', views.assignment_list, name='assignments'),
    path('<int:pk>/return/', views.asset_return, name='return'),
]
