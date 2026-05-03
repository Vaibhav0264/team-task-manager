from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:pk>/status/', views.task_update_status, name='task_update_status'),
    path('project/<int:project_pk>/new/', views.task_create, name='task_create'),
]
