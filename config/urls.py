"""URLs racine du projet TaskFlow."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('projects/', include('projects.urls')),
    path('tasks/', include('tasks.urls')),
    path('workspaces/', include('workspaces.urls')),
    path('', include('django_prometheus.urls')),
]