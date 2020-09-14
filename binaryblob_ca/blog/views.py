from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.forms import CharField
from django.forms import models as model_forms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.urls import reverse
from django.views import generic

from . import forms
from .models import BlogEntryModel, CommentModel


class IndexView(generic.ListView):
    template_name = "blog/index.html"
    paginate_by = 10

    def __init__(self):
        super().__init__()
        self.user = None
        self.page = 1

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user = User.objects.get(pk=kwargs['pk'])
        self.page = int(request.GET.get('page', 1))

    def get_queryset(self, **kwargs):
        if not self.queryset:
            self.queryset = BlogEntryModel.objects.filter(user=self.user)
        return self.queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['blog_owner'] = self.user
        max_page = ctx['page_obj'].paginator.num_pages+1
        page_range = min(max_page, 7)
        if self.page < 4:
            ctx['nav_page_range'] = list(range(1,page_range))
        elif self.page > max_page - 4:
            ctx['nav_page_range'] = list(range(max(1,max_page-page_range), max_page))
        else:
            ctx['nav_page_range'] = list(range(max(1, self.page-3), min(self.page+4, max_page)))
        ctx['menu_items'] = [{'href': reverse('blog:index', args=[self.user.pk]), 'text': 'Index'}]
        return ctx


class BlogView(generic.DetailView):
    model = BlogEntryModel

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comments"] = CommentModel.objects.filter(comment_pk_to_blog__blog__pk=self.object.pk)
        return ctx


class BlogAddView(LoginRequiredMixin, generic.CreateView):
    model = BlogEntryModel
    form_class = forms.BlogEntryForm

    def __init__(self):
        super().__init__()
        self.user = None
        self.object = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user = request.user

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["edit_mode"] = "create"
        return ctx


class BlogEditView(LoginRequiredMixin, generic.UpdateView):
    model = BlogEntryModel
    form_class = forms.BlogEntryForm

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
