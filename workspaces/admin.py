from django.contrib import admin

# Register your models here.
#from django.contrib import admin
from .models import Workspace, TeamMember

admin.site.register(Workspace)
admin.site.register(TeamMember)