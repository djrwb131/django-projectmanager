from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(BlogEntryModel)
admin.site.register(CommentModel)
admin.site.register(BlogCommentModel)
admin.site.register(BlogEditModel)
admin.site.register(CommentEditModel)
