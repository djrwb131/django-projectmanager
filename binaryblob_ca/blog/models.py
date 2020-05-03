from django.db import models
from django.contrib.auth.models import User


class BlogEntryModel(models.Model):
    user = models.ForeignKey(User, null=False)
    created_on = models.DateTimeField(auto_now_add=True, null=False)
    last_edited = models.DateTimeField(auto_now=True, null=False)
    title = models.CharField(max_length=80)
    body = models.TextField(max_length=65536)


class CommentModel(models.Model):
    user = models.ForeignKey(User, null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=False)
    last_edited = models.DateTimeField(auto_now=True, null=False)
    body = models.TextField(max_length=4096)


class BlogCommentModel(models.Model):
    blog = models.ForeignKey(BlogEntryModel, null=False)
    comment = models.ForeignKey(CommentModel, null=False)


class BlogEditModel(models.Model):
    blog_entry_edited = models.ForeignKey(BlogEntryModel, null=False)
    edit_made_by = models.ForeignKey(User, null=False)
    date_changed = models.DateTimeField(auto_now_add=True, null=False)
    old_title = models.CharField(max_length=80, null=False, blank=True)
    old_body = models.TextField(max_length=65536)


class CommentEditModel(models.Model):
    comment_edited = models.ForeignKey(CommentModel, null=False)
    edit_made_by = models.ForeignKey(User, null=False)
    date_changed = models.DateTimeField(auto_now_add=True, null=False)
    old_comment = models.TextField(max_length=4096)
