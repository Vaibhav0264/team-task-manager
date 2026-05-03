from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.projects.models import Project
from apps.tasks.models import Task
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seeds the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        # Create admin
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Ram',
                'last_name': 'Admin',
                'role': 'admin',
            }
        )
        admin.set_password('admin123')
        admin.save()
        self.stdout.write(f'  Admin: admin / admin123')

        # Create members
        for i, (first, last) in enumerate([('Shyam', 'Builder'), ('Mohit', 'Coder'), ('Manish', 'Designer')]):
            username = first.lower()
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': first,
                    'last_name': last,
                    'role': 'member',
                }
            )
            user.set_password('member123')
            user.save()
            self.stdout.write(f'  Member: {username} / member123')

        Shyam = User.objects.get(username='shyam')
        Mohit = User.objects.get(username='mohit')
        Manish = User.objects.get(username='manish')

        # Create projects
        p1, _ = Project.objects.get_or_create(
            title='Website Redesign',
            defaults={'description': 'Redesign the company website with modern UI', 'created_by': admin}
        )
        p1.members.set([Shyam, Mohit])

        p2, _ = Project.objects.get_or_create(
            title='Mobile App v2',
            defaults={'description': 'Second version of the mobile application', 'created_by': admin}
        )
        p2.members.set([Mohit, Manish])

        # Create tasks
        today = timezone.now().date()
        tasks_data = [
            {'title': 'Design homepage mockup', 'project': p1, 'status': 'done', 'priority': 'high',
             'assigned_to': Mohit, 'due_date': today - timedelta(days=5)},
            {'title': 'Implement navigation', 'project': p1, 'status': 'in_progress', 'priority': 'high',
             'assigned_to': Shyam, 'due_date': today + timedelta(days=3)},
            {'title': 'Write unit tests', 'project': p1, 'status': 'todo', 'priority': 'medium',
             'assigned_to': Shyam, 'due_date': today + timedelta(days=7)},
            {'title': 'Overdue bug fix', 'project': p1, 'status': 'todo', 'priority': 'high',
             'assigned_to': Mohit, 'due_date': today - timedelta(days=2)},
            {'title': 'Design onboarding flow', 'project': p2, 'status': 'in_progress', 'priority': 'high',
             'assigned_to': Manish, 'due_date': today + timedelta(days=2)},
            {'title': 'API integration', 'project': p2, 'status': 'todo', 'priority': 'medium',
             'assigned_to': Mohit, 'due_date': today + timedelta(days=10)},
        ]

        for td in tasks_data:
            Task.objects.get_or_create(
                title=td['title'],
                project=td['project'],
                defaults={**td, 'created_by': admin,
                          'description': f'Description for: {td["title"]}'}
            )

        self.stdout.write(self.style.SUCCESS('\nSample data created! Login credentials above.'))
