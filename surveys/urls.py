from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.survey_list, name='list'),
    path('<int:pk>/', views.survey_detail, name='detail'),
    path('create/', views.survey_create, name='create'),
    path('<int:pk>/take/', views.survey_take, name='take'),
    path('<int:pk>/results/', views.survey_results, name='results'),
]
