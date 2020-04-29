from django.db.models.signals import pre_save, pre_init
from django.dispatch import receiver
from django.utils.timezone import now

from .models import TaskModel, StatusModel


@receiver(pre_save, sender=TaskModel)
def update_task_status(sender, **kwargs):
    update_fields = kwargs["update_fields"]
    task = kwargs["instance"]

    if task.status.progress_id == 0:
        task.started_on = None
    elif task.status.progress_id <= 80:
        task.completed_on = None
    else:
        old_task = TaskModel.objects.get(pk=task.pk)
        if old_task.status != task.status:
            if old_task.status.progress_id == 0:
                if task.status.progress_id > 0:
                    task.started_on = now()
            elif old_task.status.progress_id <= 80:
                if task.status.progress_id > 80:
                    task.completed_on = now()