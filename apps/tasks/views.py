from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Task
from .forms import TaskForm, TaskStatusForm
from apps.projects.models import Project


def get_project_or_403(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if not request.user.is_admin and request.user not in project.members.all():
        messages.error(request, 'You do not have access to this project.')
        return None, project
    return project, None


@login_required
def task_list(request):
    if request.user.is_admin:
        tasks = Task.objects.select_related('project', 'assigned_to').all()
    else:
        tasks = Task.objects.filter(
            project__members=request.user
        ).select_related('project', 'assigned_to')

    status_filter = request.GET.get('status')
    project_filter = request.GET.get('project')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)

    if request.user.is_admin:
        projects = Project.objects.all()
    else:
        projects = request.user.projects.all()

    context = {
        'tasks': tasks,
        'projects': projects,
        'status_filter': status_filter,
        'project_filter': project_filter,
        'status_choices': Task.STATUS_CHOICES,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request, project_pk):
    if not request.user.is_admin:
        messages.error(request, 'Only admins can create tasks.')
        return redirect('project_detail', pk=project_pk)
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, project=project, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = TaskForm(project=project, user=request.user)
    return render(request, 'tasks/task_form.html', {'form': form, 'project': project, 'action': 'Create'})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if not request.user.is_admin and request.user not in project.members.all():
        messages.error(request, 'You do not have access to this task.')
        return redirect('task_list')
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project

    if not request.user.is_admin and request.user not in project.members.all():
        messages.error(request, 'Access denied.')
        return redirect('task_list')

    # Members can only update status of their own tasks
    if not request.user.is_admin:
        if task.assigned_to != request.user:
            messages.error(request, 'You can only update tasks assigned to you.')
            return redirect('project_detail', pk=project.pk)
        if request.method == 'POST':
            form = TaskStatusForm(request.POST, instance=task)
            if form.is_valid():
                new_status = form.cleaned_data['status']
                if not form.validate_status_transition(task.status, new_status):
                    messages.error(request, 'Invalid status transition.')
                    return redirect('task_detail', pk=task.pk)
                form.save()
                messages.success(request, 'Task status updated.')
                return redirect('project_detail', pk=project.pk)
        else:
            form = TaskStatusForm(instance=task)
        return render(request, 'tasks/task_status_form.html', {'form': form, 'task': task})

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=project, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = TaskForm(instance=task, project=project, user=request.user)
    return render(request, 'tasks/task_form.html', {'form': form, 'project': project, 'task': task, 'action': 'Edit'})


@login_required
def task_delete(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Only admins can delete tasks.')
        return redirect('task_list')
    task = get_object_or_404(Task, pk=pk)
    project_pk = task.project.pk
    if request.method == 'POST':
        name = task.title
        task.delete()
        messages.success(request, f'Task "{name}" deleted.')
        return redirect('project_detail', pk=project_pk)
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_update_status(request, pk):
    """HTMX endpoint for quick status updates."""
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if not request.user.is_admin and request.user not in project.members.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    if not request.user.is_admin and task.assigned_to != request.user:
        return JsonResponse({'error': 'Not your task'}, status=403)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in Task.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        task.status = new_status
        task.save()
        return JsonResponse({'status': task.status, 'display': task.get_status_display()})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
