from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse


def root_view(request):
    if not request.user.is_authenticated:
        return HttpResponse("no")
    return HttpResponseRedirect(reverse("blog:index", args=[request.user.pk]))
