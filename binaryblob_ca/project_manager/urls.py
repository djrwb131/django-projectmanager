from django.urls import path

from . import views, view_funcs

app_name = "project_manager"
urlpatterns = (
    path('', views.RootView.as_view(), name="root_index"),
    path('index/', views.IndexView.as_view(), name="index"),
    path('update_status/<int:pk>/', view_funcs.update_task_status, name='update_status'),
    path('rollback_status/<int:pk>/', view_funcs.rollback_task_status, name='rollback_status'),
    path('add_task/', views.AddTaskView.as_view(), name="add_task"),
    path('details/<int:pk>/', views.TaskDetailsView.as_view(), name="details"),
    path('edit_task/<int:pk>/', views.EditTaskView.as_view(), name="edit_task"),
    path('add_note/submit/<int:pk>', view_funcs.add_note_submit, name="add_note"),
    path('chat/<str:room_name>/', view_funcs.room, name="room"),
    path('checklist/',views.ChecklistView.as_view(), name="checklist"),
    path('add_checklist_item/', view_funcs.add_checklist_item, name="add_checklist_item"),
    path('edit_checklist_item/<int:pk>', view_funcs.edit_checklist_item, name="edit_checklist_item"),
    path('delete_checklist_item/<int:pk>', view_funcs.delete_checklist_item, name="delete_checklist_item"),
)
