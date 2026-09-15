from django.contrib import admin
from .models import Project, Sprint, Milestone, Goal

admin.site.register(Project)
admin.site.register(Sprint)
admin.site.register(Milestone)
admin.site.register(Goal)
