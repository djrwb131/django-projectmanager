from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import F
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.urls import reverse
from django.views import generic

from .models import TaskModel, StatusModel, TaskNoteModel


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
        ctx['most_pressing'] = TaskModel.objects.order_by('priority', F('deadline').asc(nulls_last=True))
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
    template_name = "project_manager/add_task.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


class EditTaskView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = 'project_manager.update_taskmodel'
    template_name = "project_manager/task_details.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['task'] = TaskModel.objects.get(pk=ctx['ipk'])
        ctx['notes'] = TaskNoteModel.objects.filter(task=ctx['task'])
        ctx['disabled'] = ""
        return ctx


def update_task_status(request, ipk):
    task = TaskModel.objects.get(pk=ipk)
    current = TaskModel.objects.get(pk=ipk).status
    if current.progress_id == 0:
        task.started_on = now()
    next = StatusModel.objects.filter(progress_id__gt=current.progress_id).order_by('progress_id')[0]
    if next:
        task.status = next
        task.save()
    return HttpResponseRedirect(reverse('project_manager:index'))


def rollback_task_status(request, ipk):
    task = TaskModel.objects.get(pk=ipk)
    current = TaskModel.objects.get(pk=ipk).status
    last = StatusModel.objects.filter(progress_id__lt=current.progress_id).order_by(F('progress_id').desc())[0]
    if last.progress_id == 0:
        task.started_on = None
    if last:
        task.status = last
        task.save()
    return HttpResponseRedirect(reverse('project_manager:index'))


def add_task_submit(request):
    task = TaskModel()
    update_task(task, request)
    task.status = StatusModel.objects.get(progress_id=0)
    task.save()
    messages.success(request, "Added successfully.")
    return HttpResponseRedirect(reverse('project_manager:details', args=[task.pk]))


def edit_task_submit(request, ipk):
    task = TaskModel.objects.get(pk=ipk)
    update_task(task, request)
    messages.success(request, 'Updated successfully.')
    return HttpResponseRedirect(reverse('project_manager:details', args=[ipk]))


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
    for field in post_fields:
        if field in request.POST:
            task.__dict__[field[5:]] = request.POST[field]
    for field in datetime_fields:
        if field in request.POST and not request.POST[field] == '':
            task.__dict__[field[5:]] = request.POST[field]
    if task.status is None:
        task.status = StatusModel.objects.get(progress_id=0)
    task.save()

def add_note_submit(request, ipk):
    note = TaskNoteModel()
    note.task = TaskModel.objects.get(pk=ipk)
    note.date = now()
    note.text = request.POST['task_note']
    note.save()
    return HttpResponseRedirect(reverse('project_manager:details',args=[ipk]))