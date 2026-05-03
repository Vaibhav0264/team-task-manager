from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MEMBER, 'Member'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    bio = models.TextField(blank=True)
    avatar_initials = models.CharField(max_length=3, blank=True)

    def save(self, *args, **kwargs):
        if not self.avatar_initials:
            name = self.get_full_name() or self.username
            parts = name.split()
            if len(parts) >= 2:
                self.avatar_initials = (parts[0][0] + parts[-1][0]).upper()
            else:
                self.avatar_initials = name[:2].upper()
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_member(self):
        return self.role == self.ROLE_MEMBER

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
