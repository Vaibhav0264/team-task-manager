from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .models import Project
from .forms import ProjectForm
from apps.tasks.models import Task


@login_required
def dashboard(request):
    user = request.user
    if user.is_admin:
        projects = Project.objects.prefetch_related('members', 'tasks').all()
        all_tasks = Task.objects.select_related('project', 'assigned_to').all()
        overdue_tasks = all_tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['todo', 'in_progress']
        )
        context = {
            'projects': projects,
            'total_projects': projects.count(),
            'total_tasks': all_tasks.count(),
            'todo_tasks': all_tasks.filter(status='todo').count(),
            'in_progress_tasks': all_tasks.filter(status='in_progress').count(),
            'done_tasks': all_tasks.filter(status='done').count(),
            'overdue_tasks': overdue_tasks[:5],
            'overdue_count': overdue_tasks.count(),
            'recent_tasks': all_tasks.order_by('-created_at')[:5],
        }
    else:
        user_projects = user.projects.prefetch_related('tasks').all()
        assigned_tasks = Task.objects.filter(
            assigned_to=user
        ).select_related('project').order_by('due_date')
        overdue_tasks = assigned_tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['todo', 'in_progress']
        )
        context = {
            'projects': user_projects,
            'assigned_tasks': assigned_tasks,
            'todo_tasks': assigned_tasks.filter(status='todo').count(),
            'in_progress_tasks': assigned_tasks.filter(status='in_progress').count(),
            'done_tasks': assigned_tasks.filter(status='done').count(),
            'overdue_tasks': overdue_tasks,
            'overdue_count': overdue_tasks.count(),
            'total_assigned': assigned_tasks.count(),
        }
    return render(request, 'projects/dashboard.html', context)


@login_required
def project_list(request):
    if request.user.is_admin:
        projects = Project.objects.prefetch_related('members', 'tasks').all()
    else:
        projects = request.user.projects.prefetch_related('tasks').all()
    return render(request, 'projects/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    if not request.user.is_admin:
        messages.error(request, 'Only admins can create projects.')
        return redirect('project_list')
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()
            members = form.cleaned_data.get('members', [])
            project.members.set(members)
            messages.success(request, f'Project "{project.title}" created successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Create'})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not request.user.is_admin and request.user not in project.members.all():
        messages.error(request, 'You do not have access to this project.')
        return redirect('project_list')
    tasks = project.tasks.select_related('assigned_to').order_by('status', 'due_date')
    stats = project.get_task_stats()
    context = {
        'project': project,
        'tasks': tasks,
        'stats': stats,
        'members': project.members.all(),
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_edit(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Only admins can edit projects.')
        return redirect('project_list')
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.title}" updated.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/project_form.html', {'form': form, 'action': 'Edit', 'project': project})


@login_required
def project_delete(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Only admins can delete projects.')
        return redirect('project_list')
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        name = project.title
        project.delete()
        messages.success(request, f'Project "{name}" deleted.')
        return redirect('project_list')
    return render(request, 'projects/project_confirm_delete.html', {'project': project})
