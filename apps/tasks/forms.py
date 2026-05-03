from django import forms
from .models import Task
from apps.accounts.models import User


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'status', 'priority', 'due_date', 'assigned_to')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, project=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assigned_to'].queryset = project.members.filter(is_active=True)
        self.fields['assigned_to'].empty_label = '— Unassigned —'


class TaskStatusForm(forms.ModelForm):
    """Form for members to update only task status."""
    class Meta:
        model = Task
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def validate_status_transition(self, current_status, new_status):
        valid_transitions = {
            'todo': ['todo', 'in_progress'],
            'in_progress': ['in_progress', 'todo', 'done'],
            'done': ['done', 'in_progress'],
        }
        return new_status in valid_transitions.get(current_status, [])
