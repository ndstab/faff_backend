from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register_user'),
    path('user-tasks/<str:phone_number>/', views.get_user_tasks, name='get_user_tasks'),
    path('users/', views.get_all_users, name='get-all-users'),
    path('tasks/', views.get_all_tasks, name='get-all-tasks'),
    path('tasks/<uuid:task_id>/complete/', views.complete_task, name='complete_task'),
    path('tasks/send-reminders/', views.send_reminders, name='send-reminders'),
]
