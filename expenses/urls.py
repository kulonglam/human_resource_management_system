from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.expense_list, name='list'),
    path('<int:pk>/', views.expense_detail, name='detail'),
    path('create/', views.expense_create, name='create'),
    path('<int:pk>/submit/', views.expense_submit, name='submit'),
    path('<int:pk>/approve/', views.expense_approve, name='approve'),
    path('categories/', views.category_list, name='categories'),
]
