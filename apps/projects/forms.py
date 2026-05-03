from django import forms
from .models import Project
from apps.accounts.models import User


class ProjectForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Assign Members'
    )

    class Meta:
        model = Project
        fields = ('title', 'description', 'members')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Project description'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['members'].initial = self.instance.members.all()

    def save(self, commit=True):
        project = super().save(commit=commit)
        if commit:
            members = self.cleaned_data.get('members', [])
            project.members.set(members)
        return project
