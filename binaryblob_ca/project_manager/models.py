from django.db import models
from django.contrib.auth.models import User


class StatusModel(models.Model):
    title = models.CharField(max_length=40)
    progress_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.title


# TODO: These classes are pretty devoid of member functions. A lot of stuff is in views.py that shouldn't be.

class TaskModel(models.Model):
    status = models.ForeignKey(StatusModel, on_delete=models.PROTECT, default=StatusModel.objects.get(progress_id=0).pk)
    title = models.CharField(max_length=80)
    desc = models.TextField()
    priority = models.IntegerField()
    scheduled_start = models.DateTimeField(blank=True, null=True)
    started_on = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    completed_on = models.DateTimeField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    parent_task = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.title


class ChecklistModel(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="task_checklist")
    title = models.CharField(max_length=80)
    order = models.IntegerField()
    status = models.ForeignKey(StatusModel, on_delete=models.PROTECT, default=StatusModel.objects.get(progress_id=0).pk)


class KeyphraseModel(models.Model):
    keyphrase = models.CharField(max_length=80)

    def __str__(self):
        return self.keyphrase


class TaskKeyphraseLinkModel(models.Model):
    # task which should be linked to the keyword
    root_task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="root_task")
    # specific subtask, if applicable
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, null=True, related_name="task")
    # phrase to link
    phrase = models.ForeignKey(KeyphraseModel, on_delete=models.PROTECT)


class TaskNoteModel(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="task_notes")
    text = models.TextField()
    date = models.DateTimeField()
    owner = models.ForeignKey(User, on_delete=models.PROTECT, default=User.objects.get(username="testuser").pk)

    def __str__(self):
        return "[%s]: Note on %s" % (self.task.title, self.date)


class EventModel(models.Model):
    date = models.DateTimeField()
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    old_data = models.TextField(null=True)
    new_data = models.TextField()
    table = models.CharField(max_length=64)
    field = models.CharField(null=True, max_length=64)
    r_id = models.IntegerField()

    def __str__(self):
        return "(%s #%i).%s changed by %s" % (self.table, self.r_id, self.field, self.owner)


class TaskDependencyModel(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="task_queried")
    depends_on = models.ForeignKey(TaskModel, on_delete=models.PROTECT, related_name="task_depends_on")

    def __str__(self):
        return "[%s] -> [%s]" % (self.task.title, self.depends_on.title)

# TODO: Implement task groups and alternate tasks
# An alternative group is considered complete if any task within it is complete
# Different tasks have different dependencies - being in the same alternative group
# does not imply having the same dependency path
# Tasks may depend on one or more alternative groups
# -- This is pretty complicated, so save it for later --
