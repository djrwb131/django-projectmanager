from django.db import models
from django.contrib.auth.models import User
from enum import Enum

from django.db.models import F
from django.urls import reverse


class StatusModel(models.Model):
    title = models.CharField(max_length=40)
    progress_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.title


class ChatLogModel(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    message = models.TextField()
    group_name = models.CharField(max_length=80)

    def log(self, event):
        self.user = User.objects.get(username=event['user'])
        self.message = event['message']
        self.group_name = event['group_name']
        self.save()


class TaskModel(models.Model):
    # It's very difficult to set a default here - it'll have to be dealt with as soon as the null
    # is detected somewhere else (like the form, maybe)
    #
    # Here's a simple, inelegant fix: "Just use the first one! I hope nothing changes, ever!"
    status = models.ForeignKey(StatusModel, on_delete=models.PROTECT, default=1)
    title = models.CharField(max_length=80)
    desc = models.TextField()
    priority = models.IntegerField(default=1000)
    scheduled_start = models.DateTimeField(blank=True, null=True)
    started_on = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    completed_on = models.DateTimeField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    parent_task = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)

    @staticmethod
    def get_fields_for_edit():
        f = [
            "status",
            "started_on",
            "completed_on",
        ]
        return TaskModel.get_fields_for_add() + f

    @staticmethod
    def get_fields_for_add():
        f = [
            "title",
            "parent_task",
            "owner",
            "desc",
            "priority",
            "scheduled_start",
            "deadline",
        ]
        return f

    @staticmethod
    def _retrieve_tasks_by_nearest_deadline(qs=None):
        if not qs:
            qs = TaskModel.objects.all()
        return qs.filter(status__progress_id__lt=80).order_by(
            F('deadline').asc(nulls_last=True)
        )

    @staticmethod
    def _retrieve_tasks_by_highest_priority(qs=None):
        if not qs:
            qs = TaskModel.objects.all()
        return qs.filter(status__progress_id__lt=80).order_by(
            'priority',
            F('deadline').asc(nulls_last=True)
        )

    @staticmethod
    def _retrieve_tasks_that_need_polish(qs=None):
        if not qs:
            qs = TaskModel.objects.all()
        return qs.filter(status__progress_id__exact=80).order_by(
            'priority'
        )

    @staticmethod
    def get_most_pressing(qs=None):
        ret = TaskModel._retrieve_tasks_by_nearest_deadline(qs)
        if len(ret) < 1:
            ret = TaskModel._retrieve_tasks_that_need_polish(qs)
        else:
            return ret[0]
        if len(ret) < 2:
            return None
        else:
            return ret[1]

    @staticmethod
    def get_highest_priority(qs=None):
        ret = TaskModel._retrieve_tasks_by_highest_priority(qs)
        if len(ret) < 1:
            ret = TaskModel._retrieve_tasks_that_need_polish(qs)
        else:
            return ret[0]
        if len(ret) < 3:
            return None
        else:
            return ret[2]

    @staticmethod
    def get_needs_polish(qs=None):
        ret = TaskModel._retrieve_tasks_that_need_polish(qs)
        if len(ret) < 1:
            ret = TaskModel._retrieve_tasks_by_nearest_deadline(qs)
        else:
            return ret[0]
        if len(ret) < 3:
            return None  # Nice. Have a KitKat.
        return ret[2]

    @staticmethod
    def get_incomplete_tasks(qs=None):
        if not qs:
            qs = TaskModel.objects.all()
        return qs.filter(
            status__progress_id__lt=100
        ).order_by('parent_task', F('deadline').asc(nulls_last=True),'priority')

    @staticmethod
    def get_complete_tasks(qs=None):
        if not qs:
            qs = TaskModel.objects.all()
        return qs.filter(
            status__progress_id__exact=100
        ).order_by('parent_task','priority')

    def get_absolute_url(self):
        return reverse("project_manager:details", args=[self.pk])

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
