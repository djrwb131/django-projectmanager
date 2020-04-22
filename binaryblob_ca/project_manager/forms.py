from django.forms import ModelForm
from .models import TaskModel


class AddTaskForm(ModelForm):
    class Meta:
        model = TaskModel
        fields = ['priority', 'owner', 'title', 'desc', 'parent_task', 'scheduled_start', 'deadline']
