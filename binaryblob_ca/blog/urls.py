from django.urls import path

from . import views, view_funcs

app_name = "blog"
urlpatterns = (
    path('', view_funcs.root_view, name="root"),
    path('index/<int:pk>', views.IndexView.as_view(), name="index"),
    path('add_entry/', views.BlogAddView.as_view(), name='add_entry'),
    path('details/<int:pk>', views.BlogView.as_view(), name="details"),
    path('edit/<int:pk>', views.BlogEditView.as_view(), name="edit"),
    path('add_comment/<int:pk>', view_funcs.add_comment, name="add_comment")
)
