from django.conf.global_settings import DATETIME_INPUT_FORMATS
from django.forms import ModelForm, DateTimeInput, MultiWidget, DateTimeField
from .models import TaskModel


class AddTaskForm(ModelForm):
    class Meta:
        model = TaskModel
        fields = ['priority', 'owner', 'title', 'desc', 'parent_task', 'scheduled_start', 'deadline']


# This doesn't work in safari or firefox. Need two versions
# The firefox version can use two fields and combine them after
# TODO: Have a version of this for firefox & safari - or maybe just use a more compatible version for everything
class DateTimeLocalWidget(DateTimeInput):
    input_type = "datetime-local"
    supports_microseconds = False
    format = '%Y-%m-%d %H:%M:%S'

    def format_value(self, value):
        if value:
            return value.isoformat(sep="T")
        return None


class DateTimeLocalField(DateTimeField):
    widget = DateTimeLocalWidget
    supports_microseconds = False

    def clean(self, value):
        if len(value) == 0:
            return None
        return value.replace("T", " ")


class EditTaskForm(ModelForm):
    class Meta:
        model = TaskModel
        fields = [x.name for x in model._meta.fields]
        field_classes = {
            'scheduled_start': DateTimeLocalField,
            'started_on': DateTimeLocalField,
            'deadline': DateTimeLocalField,
            'completed_on': DateTimeLocalField,
        }