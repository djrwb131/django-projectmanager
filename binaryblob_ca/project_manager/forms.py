from django.forms import ModelForm
from .models import TaskModel


class AddTaskForm(ModelForm):
    class Meta:
        model = TaskModel
        fields = ['priority', 'owner', 'title', 'desc', 'parent_task', 'scheduled_start', 'deadline']


class EditTaskForm(ModelForm):
    class Meta:
        model = TaskModel
        fields = [x.name for x in model._meta.fields]
