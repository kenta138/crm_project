from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/dashboard/", permanent=False)),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("clients.urls")),
    path("", include("contacts.urls")),
    path("", include("tasks.urls")),
    path("", include("labels.urls")),
    path("", include("reports.urls")),
]
