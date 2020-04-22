from django.db import models
from django.contrib.auth.models import User
from enum import Enum

from django.db.models import F


class StatusModel(models.Model):
    title = models.CharField(max_length=40)
    progress_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.title


# TODO: This seems like an ok way to deal with the default issue. Is there a better way though?
try:
    STATUS_DEFAULT = StatusModel.objects.get(progress_id=0)
except StatusModel.DoesNotExist:
    a = StatusModel()
    a.title = "Default!!"
    a.progress_id = 0
    a.save()


class TaskModel(models.Model):
    status = models.ForeignKey(StatusModel, on_delete=models.PROTECT, default=STATUS_DEFAULT)
    title = models.CharField(max_length=80)
    desc = models.TextField()
    priority = models.IntegerField()
    scheduled_start = models.DateTimeField(blank=True, null=True)
    started_on = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    completed_on = models.DateTimeField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    parent_task = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    def _retrieve_tasks_by_nearest_deadline(self):
        return self.objects.filter(status__progress_id__lt=80).order_by(
            F('deadline').asc(nulls_last=True)
        )

    def _retrieve_tasks_by_highest_priority(self):
        return self.objects.filter(status__progress_id__lt=80).order_by(
            'priority',
            F('deadline').asc(nulls_last=True)
        )

    def _retrieve_tasks_that_need_polish(self):
        return self.objects.filter(status__progress_id__exact=80).order_by(
            'priority'
        )

    def get_most_pressing(self):
        ret = self._retrieve_tasks_by_nearest_deadline()
        if len(ret) < 1:
            ret = self._retrieve_tasks_that_need_polish()
        else:
            return ret[0]
        if len(ret) < 2:
            return None
        else:
            return ret[1]

    def get_highest_priority(self):
        ret = self._retrieve_tasks_by_highest_priority()
        if len(ret) < 1:
            ret = self._retrieve_tasks_that_need_polish()
        else:
            return ret[0]
        if len(ret) < 3:
            return None
        else:
            return ret[2]

    def get_needs_polish(self):
        ret = self._retrieve_tasks_that_need_polish()
        if len(ret) < 1:
            ret = self._retrieve_tasks_by_nearest_deadline()
        else:
            return ret[0]
        if len(ret) < 3:
            return None  # Nice. Have a KitKat.
        return ret[2]

    def get_incomplete_tasks(self):
        return self.objects.filter(
            status__progress_id__lt=100
        ).order_by(F('deadline').asc(nulls_last=True))

    def get_complete_tasks(self):
        return self.objects.filter(
            status__progress_id__exact=100
        ).order_by('priority')

    def __str__(self):
        return self.title


class Permissions(Enum):
    VIEW = 1
    EDIT = 2
    CREATE = 4
    DELETE = 8


# TODO: THIS NEEDS TO BE PROTECTED!
class TaskPermissionModel(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="user_permissions")
    perms = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_permissions")

    def has_permission(self, perm):
        if perm not in Permissions:
            raise ValueError("Permission with id %i does not exist!" % (perm))
        return self.perms & perm > 0

    def add_permission(self, perm):
        if perm not in Permissions:
            raise ValueError("Permission with id %i does not exist!" % (perm))
        self.perms = self.perms | perm

    def del_permission(self, perm):
        if perm not in Permissions:
            raise ValueError("Permission with id %i does not exist!" % (perm))
        self.perms = self.perms ^ perm


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
