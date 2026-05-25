from django.urls import path
from . import views

app_name = 'exits'

urlpatterns = [
    path('', views.exit_list, name='list'),
    path('<int:pk>/', views.exit_detail, name='detail'),
    path('create/', views.exit_create, name='create'),
    path('<int:pk>/update/', views.exit_update, name='update'),
    path('<int:exit_id>/checklist/add/', views.checklist_add, name='checklist_add'),
    path('checklist/<int:pk>/update/', views.checklist_update, name='checklist_update'),
]
