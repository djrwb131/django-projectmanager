# Non class-based views, and their supporting functions
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.timezone import now

from .models import EventModel, TaskModel, StatusModel, TaskNoteModel


def log_event(obj, owner, field, old_value, new_value):
    event = EventModel()
    if obj.pk:
        event.r_id = obj.pk
    elif obj.task.pk:
        event.r_id = obj.task.pk
    event.table = obj._meta.db_table
    event.field = field
    event.old_data = old_value
    event.new_data = new_value
    event.date = now()
    event.owner = owner
    event.save()


def log_event_post(user, obj, field, req_field):
    log_event(obj, user, field, obj.__dict__[field], request.POST[req_field])


def log_status_update(user, task, status):
    log_event(task, user, "status", task.status, status)


def log_changed_fields(user, obj, changed_fields):
    for f in changed_fields:
        log_event(obj, user, f[0], f[1], f[2])


def log_new_task(user, task):
    log_event(task, user, "", "", "Created object")


def update_task_status(request, pk):
    task = TaskModel.objects.get(pk=pk)
    current = TaskModel.objects.get(pk=pk).status

    if current.progress_id == 0:
        s = now()
        log_event(task, request.user, "started_on", task.started_on, s)
        task.started_on = s

    next_status = StatusModel.objects.filter(progress_id__gt=current.progress_id).order_by('progress_id')
    if next_status:
        log_status_update(request.user, task, next_status[0])
        task.status = next_status[0]
        task.save()
    return HttpResponseRedirect(reverse('project_manager:index'))


def rollback_task_status(request, pk):
    task = TaskModel.objects.get(pk=pk)
    current = TaskModel.objects.get(pk=pk).status
    last = StatusModel.objects.filter(progress_id__lt=current.progress_id).order_by(F('progress_id').desc())[0]
    if last.progress_id == 0:
        log_event(task, request.user, "started_on", task.started_on, None)
        task.started_on = None
    if last:
        log_status_update(request.user, task, last)
        task.status = last
        task.save()
    return HttpResponseRedirect(reverse('project_manager:index'))


def add_note_submit(request, pk):
    note = TaskNoteModel()
    note.task = TaskModel.objects.get(pk=pk)
    note.date = now()
    note.text = request.POST['task_note']
    note.owner = request.user
    note.save()

    return HttpResponseRedirect(reverse('project_manager:details', args=[pk]))
