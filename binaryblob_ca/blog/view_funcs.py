from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from .models import CommentModel, BlogCommentModel, BlogEntryModel


def root_view(request):
    if not request.user.is_authenticated:
        return HttpResponse("Please log in first.")
    return HttpResponseRedirect(reverse("blog:index", args=[request.user.pk]))


def add_comment(request, pk):
    comment = CommentModel()
    if request.user.is_authenticated:
        comment.user = request.user
    else:
        comment.user = AnonymousUser
    comment.body = request.POST["comment_text"]
    comment.save()

    link = BlogCommentModel()
    link.blog = BlogEntryModel.objects.get(pk=pk)
    link.comment = comment
    link.save()

    return HttpResponseRedirect(request.POST["redirect_to"])
