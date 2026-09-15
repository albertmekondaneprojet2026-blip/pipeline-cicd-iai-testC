from django.contrib import admin
from .models import Workspace, TeamMember, UserPreference

admin.site.register(Workspace)
admin.site.register(TeamMember)
admin.site.register(UserPreference)
