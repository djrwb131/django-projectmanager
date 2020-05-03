from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import generic

from .models import BlogEntryModel


class IndexView(generic.ListView):
    template_name = "blog/index.html"
    model = BlogEntryModel

    def get_queryset(self):
        if not self.queryset:
            self.queryset = self.model.objects.filter(user=kwargs['pk'])
        return self.queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blog_owner'] = User.objects.get(pk=kwargs['pk'])
        return ctx


class BlogView(generic.DetailView):
    model = BlogEntryModel


class BlogAddView(LoginRequiredMixin, generic.CreateView):
    model = BlogEntryModel

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["edit_mode"] = "create"
        return ctx


class BlogEditView(LoginRequiredMixin, generic.UpdateView):
    model = BlogEntryModel

    def get(self, request, *args, **kwargs):
        if not request.user == User.objects.get(pk=kwargs['pk']):
            return HttpResponse("no", 403)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["edit_mode"] = "update"
        return ctx