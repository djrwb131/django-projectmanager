from django.db import models


class StatusModel(models.Model):
    title = models.CharField(max_length=40)
    progress_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.title


class TaskModel(models.Model):
    status = models.ForeignKey(StatusModel, on_delete=models.PROTECT,default=StatusModel.objects.get(progress_id=0))
    title = models.CharField(max_length=80)
    desc = models.TextField()
    priority = models.IntegerField()
    scheduled_start = models.DateTimeField(blank=True, null=True)
    started_on = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    completed_on = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title


class TaskNoteModel(models.Model):
    task = models.ForeignKey(TaskModel,on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField()

    def __str__(self):
        return "[%s]: Note on %s" % (self.task.title, self.date)


class TaskDependencyModel(models.Model):
    task = models.ForeignKey(TaskModel,on_delete=models.CASCADE,related_name="task_queried")
    depends_on = models.ForeignKey(TaskModel,on_delete=models.PROTECT,related_name="task_depends_on")


#TODO: Implement task groups and alternate tasks
# An alternative group is considered complete if any task within it is complete
# Different tasks have different dependencies - being in the same alternative group
# does not imply having the same dependency path
# Tasks may depend on one or more alternative groups
# -- This is pretty complicated, so save it for later --