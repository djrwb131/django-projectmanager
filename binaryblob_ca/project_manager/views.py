from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import F
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.urls import reverse
from django.views import generic

from .models import TaskModel, StatusModel, TaskNoteModel, EventModel


# views need to do this stuff:
# - Index (summary of tasks) - done
# - Details (specific task) - done
# - Add task - done
# - Edit task - done
# - Update task status - done

class IndexView(generic.TemplateView):
    template_name = "project_manager/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['most_pressing'] = TaskModel.objects.filter(status__progress_id__lt=80).order_by(
            F('deadline').asc(nulls_last=True)
        )[0]
        ctx['highest_priority'] = TaskModel.objects.filter(status__progress_id__lt=80).order_by(
            'priority',
            F('deadline').asc(nulls_last=True)
        )[0]
        ctx['needs_polish'] = TaskModel.objects.filter(status__progress_id__exact=80).order_by(
            'priority'
        )[0]
        ctx['incomplete_tasks'] = TaskModel.objects.filter(
            status__progress_id__lt=100
        ).order_by(F('deadline').asc(nulls_last=True))
        ctx['complete_tasks'] = TaskModel.objects.filter(
            status__progress_id__exact=100
        ).order_by('priority')
        return ctx


class TaskDetailsView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = "project_manager.view_taskmodel"
    template_name = "project_manager/task_details.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['task'] = TaskModel.objects.get(pk=kwargs['ipk'])
        ctx['notes'] = TaskNoteModel.objects.filter(task=ctx['task'])
        ctx['disabled'] = "disabled"
        return ctx


class AddTaskView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = 'project_manager.add_taskmodel'
    template_name = "project_manager/task_details.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['disabled'] = ""
        ctx['edit_mode'] = "add"
        return ctx


class EditTaskView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = 'project_manager.update_taskmodel'
    template_name = "project_manager/task_details.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['task'] = TaskModel.objects.get(pk=ctx['ipk'])
        ctx['notes'] = TaskNoteModel.objects.filter(task=ctx['task'])
        ctx['disabled'] = ""
        ctx['edit_mode'] = "edit"
        return ctx


def log_event_post(request,obj,field,req_field):
    event = EventModel()
    event.r_id = obj.pk
    event.table = obj._meta.db_table
    event.old_data = obj.__dict__[field]
    event.new_data = request.POST[req_field]
    event.date = now()
    event.owner = request.user
    event.save()


def log_status_update(request,task,status):
    event = EventModel()
    event.r_id = task.pk
    event.table = task._meta.db_table
    event.old_data = task.status
    event.new_data = status
    event.date = now()
    event.owner = request.user
    event.save()


def update_task_status(request, ipk):
    task = TaskModel.objects.get(pk=ipk)
    current = TaskModel.objects.get(pk=ipk).status

    if current.progress_id == 0:
        request.POST["started_on"] = now()
        log_event_post(request,task,"started_on","started_on")
        task.started_on = now()

    next_status = StatusModel.objects.filter(progress_id__gt=current.progress_id).order_by('progress_id')
    if next_status:
        log_status_update(request, task, next_status[0])
        task.status = next_status[0]
        task.save()
    return HttpResponseRedirect(reverse('project_manager:index'))


def rollback_task_status(request, ipk):
    task = TaskModel.objects.get(pk=ipk)
    current = TaskModel.objects.get(pk=ipk).status
    last = StatusModel.objects.filter(progress_id__lt=current.progress_id).order_by(F('progress_id').desc())[0]
    if last.progress_id == 0:
        request.POST["started_on"] = None
        log_event_post(request,task,"started_on","started_on")
        task.started_on = None
    if last:
        log_status_update(request, task, last)
        task.status = last
        task.save()
    return HttpResponseRedirect(reverse('project_manager:index'))


def log_new_task(request,task):
    event = EventModel()
    event.table = task._meta.db_table
    event.r_id = task.pk
    event.old_data = "None"
    event.new_data = "Object was created"
    event.date = now()
    event.owner = request.user
    event.save()


def add_task_submit(request):
    task = TaskModel()
    update_task(task, request)
    task.status = StatusModel.objects.get(progress_id=0)
    task.save()
    log_new_task(request,task)

    messages.success(request, "Added successfully.")
    return HttpResponseRedirect(reverse('project_manager:details', args=[task.pk]))


def edit_task_submit(request, ipk):
    task = TaskModel.objects.get(pk=ipk)
    update_task(task, request)
    messages.success(request, 'Updated successfully.')
    return HttpResponseRedirect(reverse('project_manager:details', args=[ipk]))


def log_changed_fields(request,obj,changed_fields):
    for f in changed_fields:
        event = EventModel()
        obj_f = f[0]
        old_v = f[1]
        new_v = f[2]
        event.table = obj._meta.db_table
        event.r_id = obj.pk
        event.field = obj_f
        event.old_data = old_v
        event.new_data = new_v
        event.date = now()
        event.owner = request.user
        event.save()


def update_task(task, request):
    post_fields = (
        'task_status',
        'task_title',
        'task_desc',
        'task_priority',
    )
    # these fields make errors if they're blank and not null...
    datetime_fields = (
        'task_scheduled_start',
        'task_started_on',
        'task_deadline',
        'task_completed_on',
    )
    changed_fields = []
    for field in post_fields:
        if field in request.POST:
            if not task.__dict__[field[5:]] == request.POST[field]:
                changed_fields.append((field[5:],task.__dict__[field[5:]],request.POST[field],))
                task.__dict__[field[5:]] = request.POST[field]
    for field in datetime_fields:
        if field in request.POST and not request.POST[field] == '':
            if not task.__dict__[field[5:]] == request.POST[field]:
                changed_fields.append((field,task.__dict__[field[5:]],request.POST[field],))
                task.__dict__[field[5:]] = request.POST[field]
    next_status = None
    if task.status is None:
        next_status = StatusModel.objects.get(progress_id=0)
        task.status = next_status
    task.save()
    log_changed_fields(request,task,changed_fields)
    if next_status:
        log_status_update(request, task, next_status)


def add_note_submit(request, ipk):
    note = TaskNoteModel()
    note.task = TaskModel.objects.get(pk=ipk)
    note.date = now()
    note.text = request.POST['task_note']
    note.owner = request.user
    note.save()

    return HttpResponseRedirect(reverse('project_manager:details',args=[ipk]))