from rest_framework import serializers
from apps.accounts.models import User
from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Task


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'avatar_initials')
        read_only_fields = ('id', 'avatar_initials', 'role')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'password')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ('id', 'user', 'joined_at')


class ProjectSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True,
        source='members', required=False
    )
    task_stats = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'created_at', 'updated_at',
                  'created_by', 'members', 'member_ids', 'task_stats')
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def get_task_stats(self, obj):
        return obj.get_task_stats()

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        project = Project.objects.create(**validated_data)
        project.members.set(members)
        return project

    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if members is not None:
            instance.members.set(members)
        return instance


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True,
        source='assigned_to', required=False, allow_null=True
    )
    created_by = UserSerializer(read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'status', 'priority', 'due_date',
                  'created_at', 'updated_at', 'project', 'project_title',
                  'assigned_to', 'assigned_to_id', 'created_by', 'is_overdue')
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def validate(self, data):
        request = self.context.get('request')
        project = data.get('project', getattr(self.instance, 'project', None))

        # Only validate assigned_to if it's being set
        assigned_to = data.get('assigned_to')
        if assigned_to and project:
            if assigned_to not in project.members.all():
                raise serializers.ValidationError(
                    {'assigned_to': 'User must be a member of the project.'}
                )

        # Members can only update status
        if request and not request.user.is_admin:
            if self.instance:
                allowed_fields = {'status'}
                changing = set(data.keys()) - allowed_fields
                if changing:
                    raise serializers.ValidationError(
                        'Members can only update task status.'
                    )
                if self.instance.assigned_to != request.user:
                    raise serializers.ValidationError(
                        'You can only update tasks assigned to you.'
                    )
        return data


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('status',)

    def validate_status(self, value):
        valid = [s[0] for s in Task.STATUS_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(f'Invalid status. Choose from: {valid}')
        return value
