from django.contrib import admin
from .models import Project, ProjectMembership

class MembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    inlines = [MembershipInline]
