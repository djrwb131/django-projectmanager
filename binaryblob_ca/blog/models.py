from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class BlogEntryModel(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=True, null=False)
    last_edited = models.DateTimeField(auto_now=True, null=False)
    title = models.CharField(max_length=80)
    body = models.TextField(max_length=65536)

    def get_absolute_url(self):
        return reverse("blog:details", args=[self.pk])

    def str(self):
        return self.title


class CommentModel(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.PROTECT)
    created_on = models.DateTimeField(auto_now_add=True, null=False)
    last_edited = models.DateTimeField(auto_now=True, null=False)
    body = models.TextField(max_length=4096)

    def str(self):
        if len(self.body) > 30:
            return self.body[:27] + "..."
        return self.body


class BlogCommentModel(models.Model):
    blog = models.ForeignKey(BlogEntryModel, on_delete=models.PROTECT, null=False, related_name="comments_with_blog_pk")
    comment = models.ForeignKey(CommentModel, on_delete=models.PROTECT, null=False, related_name="comment_pk_to_blog")


class BlogEditModel(models.Model):
    blog_entry_edited = models.ForeignKey(BlogEntryModel, on_delete=models.PROTECT, null=False)
    edit_made_by = models.ForeignKey(User, on_delete=models.PROTECT, null=False)
    date_changed = models.DateTimeField(auto_now_add=True, null=False)
    old_title = models.CharField(max_length=80, null=False, blank=True)
    old_body = models.TextField(max_length=65536)


class CommentEditModel(models.Model):
    comment_edited = models.ForeignKey(CommentModel, on_delete=models.PROTECT, null=False)
    edit_made_by = models.ForeignKey(User, on_delete=models.PROTECT, null=False)
    date_changed = models.DateTimeField(auto_now_add=True, null=False)
    old_comment = models.TextField(max_length=4096)
