from django.db import models
from django.conf import settings
from django.utils import timezone


class Task(models.Model):
    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_DONE, 'Done'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )

    class Meta:
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"

    @property
    def is_overdue(self):
        if self.due_date and self.status != self.STATUS_DONE:
            return self.due_date < timezone.now().date()
        return False

    @property
    def status_badge_class(self):
        return {
            'todo': 'badge-todo',
            'in_progress': 'badge-progress',
            'done': 'badge-done',
        }.get(self.status, 'badge-secondary')

    @property
    def priority_badge_class(self):
        return {
            'low': 'badge-low',
            'medium': 'badge-medium',
            'high': 'badge-high',
        }.get(self.priority, 'badge-secondary')
