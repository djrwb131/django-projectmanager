# Class-based views

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.views import generic

from .forms import AddTaskForm, EditTaskForm
from .models import TaskModel, TaskNoteModel
from .view_funcs import log_new_task, log_changed_fields


class IndexView(generic.ListView):
    template_name = "project_manager/index.html"
    model = TaskModel
    allow_empty = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = None

    def setup(self, request, *args, **kwargs):
        self.user = request.user
        return super().setup(request, *args, **kwargs)

    def get_queryset(self):
        if not self.queryset:
            if self.user.is_anonymous:
                self.queryset = self.model.objects.filter(Q(owner=None))
            else:
                self.queryset = self.model.objects.filter(Q(owner=self.user) | Q(owner=None))
        return self.queryset

    def get_context_data(self, **kwargs):
        qs = self.get_queryset()
        ctx = super().get_context_data(**kwargs)

        # I've no idea. Don't ask, it just works.
        ctx['most_pressing'] = self.model.get_most_pressing(self.model, qs)
        ctx['highest_priority'] = self.model.get_highest_priority(self.model, qs)
        ctx['needs_polish'] = self.model.get_needs_polish(self.model, qs)
        ctx['incomplete_tasks'] = self.model.get_incomplete_tasks(self.model, qs)
        ctx['complete_tasks'] = self.model.get_complete_tasks(self.model, qs)

        return ctx


class TaskDetailsView(PermissionRequiredMixin, generic.DetailView):
    permission_required = "project_manager.view_taskmodel"
    model = TaskModel
    notes_model = TaskNoteModel

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['notes'] = self.notes_model.objects.filter(task=self.object)
        ctx['dependencies'] = self.model.objects.filter(task_depends_on__task=self.object)
        return ctx


class AddTaskView(PermissionRequiredMixin, generic.CreateView):
    permission_required = 'project_manager.add_taskmodel'
    form_class = AddTaskForm
    model = TaskModel

    # url = reverse("project_manager:index")

    def __init__(self):
        super().__init__()
        self.object = self.model()
        self.user = None

    def setup(self, request, *args, **kwargs):
        self.user = request.user
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['edit_mode'] = "add"
        return ctx

    def form_valid(self, form):
        resp = super().form_valid(form)
        log_new_task(self.user, self.object)
        messages.success(self.request, "Task added successfully.")
        return resp


class EditTaskView(PermissionRequiredMixin, generic.edit.UpdateView):
    permission_required = 'project_manager.update_taskmodel'
    form_class = EditTaskForm
    model = TaskModel
    notes_model = TaskNoteModel

    def __init__(self):
        super().__init__()
        self.user = None

    def setup(self, request, *args, **kwargs):
        self.user = request.user
        return super().setup(request, *args, **kwargs)

    def form_valid(self, form):
        changed_fields = []
        if form.has_changed():
            for f in form.changed_data:
                changed_fields.append((f, form.initial[f], form.cleaned_data[f]))
        resp = super().form_valid(form)
        log_changed_fields(self.user, self.object, changed_fields)
        messages.success(self.request, "Edit was successful.")
        return resp

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['edit_mode'] = "edit"
        ctx['notes'] = self.notes_model.objects.filter(task=self.object)
        return ctx
