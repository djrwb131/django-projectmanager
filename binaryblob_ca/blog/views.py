from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.forms import CharField
from django.forms import models as model_forms
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import generic

from .models import BlogEntryModel, CommentModel


class IndexView(generic.ListView):
    template_name = "blog/index.html"

    def __init__(self):
        super().__init__()
        self.user = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user = User.objects.get(pk=kwargs['pk'])

    def get_queryset(self, **kwargs):
        if not self.queryset:
            self.queryset = BlogEntryModel.objects.filter(user=self.user)
        return self.queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blog_owner'] = self.user
        return ctx


class BlogView(generic.DetailView):
    model = BlogEntryModel

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comments"] = CommentModel.objects.filter(comment_pk_to_blog__blog__pk=self.object.pk)
        return ctx


class BlogAddView(LoginRequiredMixin, generic.CreateView):
    model = BlogEntryModel
    fields = ["title", "body"]

    def __init__(self):
        super().__init__()
        self.user = None
        self.object = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user = request.user

    def post(self, request, *args, **kwargs):
        # a bit complicated - is there a better way?
        fields = self.fields
        fields.append("user")
        form_class = model_forms.modelform_factory(self.model, fields=fields)
        post = request.POST.copy()
        post["user"] = request.user
        form = form_class(post)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["edit_mode"] = "create"
        return ctx


class BlogEditView(LoginRequiredMixin, generic.UpdateView):
    model = BlogEntryModel
    fields = ["title", "body"]

    def get(self, request, *args, **kwargs):
        try:
            blog_owner = self.model.objects.get(pk=kwargs['pk']).user
        except BlogEntryModel.DoesNotExist:
            return HttpResponse("%s is not permitted to edit this blog entry." % request.user)
        if not request.user == blog_owner:
            return HttpResponse("%s is not permitted to edit this blog entry." % request.user)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["edit_mode"] = "update"
        return ctx
