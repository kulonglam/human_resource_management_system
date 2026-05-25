from django.urls import path
from . import views

app_name = 'discipline'

urlpatterns = [
    path('', views.discipline_list, name='list'),
    path('<int:pk>/', views.discipline_detail, name='detail'),
    path('create/', views.discipline_create, name='create'),
    path('<int:pk>/update/', views.discipline_update, name='update'),
    path('<int:discipline_id>/appeal/', views.appeal_create, name='appeal'),
    path('appeal/<int:pk>/review/', views.appeal_review, name='appeal_review'),
]
