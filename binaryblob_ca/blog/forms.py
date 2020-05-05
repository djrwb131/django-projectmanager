from django import forms

from .models import BlogEntryModel


class BlogEntryForm(forms.ModelForm):
    class Meta:
        model = BlogEntryModel
        fields = ["title", "body"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs["class"] = "form-control"
        self.fields["body"].widget.attrs["class"] = "form-control"
        self.fields["body"].widget.attrs["style"] = "resize: none;"

