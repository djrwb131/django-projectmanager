from django.urls import path

from . import views

app_name = "project_manager"
urlpatterns = (
    path('', views.IndexView.as_view(), name="index"),
    path('update_status/<int:pk>/', views.update_task_status, name='update_status'),
    path('rollback_status/<int:pk>/', views.rollback_task_status, name='rollback_status'),
    path('add_task/', views.AddTaskView.as_view(), name="add_task"),
    path('details/<int:pk>/', views.TaskDetailsView.as_view(), name="details"),
    path('edit_task/<int:pk>/', views.EditTaskView.as_view(), name="edit_task"),
    path('add_note/submit/<int:pk>', views.add_note_submit, name="add_note"),
)
