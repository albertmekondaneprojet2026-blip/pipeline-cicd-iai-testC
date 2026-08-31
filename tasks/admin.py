from django.contrib import admin

# Register your models here.
#from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'estimated_hours', 'is_blocked', 'assignee')
    list_filter = ('status', 'is_blocked', 'project')