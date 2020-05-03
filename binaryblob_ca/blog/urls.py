from django.urls import path

from . import views, view_funcs

app_name = "project_manager"
urlpatterns = (
    path('', view_funcs.root_view, name="root_index"),
    path('index/<int:pk>', views.IndexView.as_view(), name="index"),
    path('add_entry/', view_funcs.BlogEditView.as_view(), name='add_entry'),
    path('details/<int:pk>', views.BlogView.as_view())
)
