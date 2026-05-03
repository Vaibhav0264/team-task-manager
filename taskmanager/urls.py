from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.projects.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('api/', include('apps.api.urls')),
]
