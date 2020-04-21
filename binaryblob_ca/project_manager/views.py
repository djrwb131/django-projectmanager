from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.db.models import F
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.urls import reverse
from django.views import generic

from .models import TaskModel, StatusModel, TaskNoteModel, EventModel, TaskDependencyModel


# views need to do this stuff:
# - Index (summary of tasks) - done
# - Details (specific task) - done
# - Add task - done
# - Edit task - done
# - Update task status - done

#TODO: half of this shouldn't be in views.py - a lot of this belongs in the model
#TODO: we're only using TemplateView. There are better options.
class IndexView(generic.TemplateView):
    template_name = "project_manager/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mp = TaskModel.objects.filter(status__progress_id__lt=80).order_by(
            F('deadline').asc(nulls_last=True)
        )
        mpi = 0
        hp = TaskModel.objects.filter(status__progress_id__lt=80).order_by(
            'priority',
            F('deadline').asc(nulls_last=True)
        )
        hpi = 0
        np =  TaskModel.objects.filter(status__progress_id__exact=80).order_by(
            'priority'
        )
        npi = 0

        # mp, hp, np
        ctx['most_pressing'] = None
        if len(mp)-mpi > 0:
            ctx['most_pressing'] = mp[mpi]
            mpi += 1
        if ctx['most_pressing'] is None:
            if len(hp)-hpi > 0:
                ctx['most_pressing'] = hp[hpi]
                hpi += 1
            elif len(np)-npi >0:
                ctx['most_pressing'] = np[npi]
                npi += 1

        #hp, mp, np
        ctx['highest_priority'] = None
        if len(hp)-hpi > 0:
            ctx['highest_priority'] = hp[hpi]
            hpi += 1
        if ctx['highest_priority'] is None:
            if len(mp)-mpi > 0:
                ctx['highest_priority'] = mp[mpi]
                mpi += 1
            elif len(np)-npi >0:
                ctx['highest_priority'] = np[npi]
                npi += 1

        # np, mp, hp
        ctx['needs_polish'] = None
        if len(np)-npi > 0:
            ctx['needs_polish'] = np[npi]
            npi += 1
        if ctx['needs_polish'] is None:
            if len(mp)-mpi > 0:
                ctx['needs_polish'] = mp[mpi]
                mpi += 1
            elif len(hp)-hpi >0:
                ctx['needs_polish'] = hp[hpi]
                hpi += 1

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
        ctx['dependencies'] = TaskModel.objects.filter(task_depends_on__task__id=ctx['ipk'])
        return ctx


class AddTaskView(PermissionRequiredMixin, generic.TemplateView):
    permission_required = 'project_manager.add_taskmodel'
    template_name = "project_manager/task_details.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['disabled'] = ""
        ctx['all_tasks'] = TaskModel.objects.all()
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
        ctx['all_tasks'] = TaskModel.objects.exclude(pk=kwargs['ipk'])
        ctx['dependencies'] = TaskModel.objects.filter(task_depends_on__task__id=ctx['ipk'])
        return ctx


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


def log_event_post(request, obj, field, req_field):
    log_event(obj, request.user, field, obj.__dict__[field], request.POST[req_field])


def log_status_update(request, task, status):
    log_event(task, request.user, "status", task.status, status)


def log_changed_fields(request, obj, changed_fields):
    for f in changed_fields:
        log_event(obj, request.user, f[0], f[1], f[2])


def log_new_task(request, task):
    log_event(task, request.user, "", "", "Created object")


def update_task_status(request, ipk):
    task = TaskModel.objects.get(pk=ipk)
    current = TaskModel.objects.get(pk=ipk).status

    if current.progress_id == 0:
        s = now()
        log_event(task, request.user, "started_on", task.started_on, s)
        task.started_on = s

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
        log_event(task, request.user, "started_on", task.started_on, None)
        task.started_on = None
    if last:
        log_status_update(request, task, last)
        task.status = last
        task.save()
    return HttpResponseRedirect(reverse('project_manager:index'))


def add_task_submit(request):
    task = TaskModel()
    update_task(task, request)
    task.status = StatusModel.objects.get(progress_id=0)
    task.save()
    log_new_task(request, task)

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
    changed_fields = []
    for field in post_fields:
        if field in request.POST:
            if not task.__dict__[field[5:]] == request.POST[field]:
                changed_fields.append((field[5:], task.__dict__[field[5:]], request.POST[field],))
                task.__dict__[field[5:]] = request.POST[field]
    for field in datetime_fields:
        if field in request.POST and not request.POST[field] == '':
            if not task.__dict__[field[5:]] == request.POST[field]:
                changed_fields.append((field, task.__dict__[field[5:]], request.POST[field],))
                task.__dict__[field[5:]] = request.POST[field]
    next_status = None
    if task.status is None:
        next_status = StatusModel.objects.get(progress_id=0)
        task.status = next_status
    log_changed_fields(request, task, changed_fields)
    if next_status:
        log_status_update(request, task, next_status)
    parent_task = request.POST.get("task_parent", None)
    if parent_task:
        log_event(task, request.user, "parent_task", task.parent_task, parent_task)
        task.parent_task = TaskModel.objects.get(pk=parent_task)
    task.save()

    #TODO: task dependencies can only be added or removed one at a time...
    cur_deps = TaskDependencyModel.objects.filter(task=task)
    task_dep_add = request.POST.get('task_deps',None)
    task_dep_remove = request.POST.get('task_deps_remove',None)
    task_new_owner = request.POST.get('task_owner',None)
    if task_dep_remove:
        cur_deps.filter(depends_on=dep_tasks).delete()
        cur_deps.save()
    if task_dep_add:
        b = TaskDependencyModel()
        b.task = task
        b.depends_on = TaskModel.objects.get(pk=task_dep_add)
        b.save()
    if task_new_owner:
        try:
            a = task.owner
            task.owner = User.objects.get(username=task_new_owner)
            log_event(task, request.user, "owner", a, task_new_owner)
        except User.DoesNotExist:
            messages.error(request,"Owner was not updated: No such user!")


def add_note_submit(request, ipk):
    note = TaskNoteModel()
    note.task = TaskModel.objects.get(pk=ipk)
    note.date = now()
    note.text = request.POST['task_note']
    note.owner = request.user
    note.save()

    return HttpResponseRedirect(reverse('project_manager:details', args=[ipk]))
