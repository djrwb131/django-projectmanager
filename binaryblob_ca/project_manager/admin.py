from django.contrib import admin

from .models import *

admin.site.register(StatusModel)
admin.site.register(TaskModel)
admin.site.register(TaskNoteModel)
admin.site.register(TaskDependencyModel)
