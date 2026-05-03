from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.accounts.models import User
from apps.projects.models import Project
from apps.tasks.models import Task
from .serializers import (
    UserSerializer, UserCreateSerializer,
    ProjectSerializer, TaskSerializer, TaskStatusUpdateSerializer
)
from .permissions import IsAdminUser, IsAdminOrReadOnly, IsProjectMemberOrAdmin, CanEditTask


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action == 'me':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Project.objects.prefetch_related('members', 'tasks').all()
        return user.projects.prefetch_related('tasks').all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        project = self.get_object()
        tasks = project.tasks.select_related('assigned_to').all()
        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def add_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        project.members.add(user)
        return Response({'status': f'{user.username} added to project.'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def remove_member(self, request, pk=None):
        project = self.get_object()
        user_id = request.data.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        project.members.remove(user)
        return Response({'status': f'{user.username} removed from project.'})


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at', 'status', 'priority']

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), CanEditTask()]
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [IsAuthenticated(), IsProjectMemberOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            qs = Task.objects.select_related('project', 'assigned_to', 'created_by').all()
        else:
            qs = Task.objects.filter(
                project__members=user
            ).select_related('project', 'assigned_to', 'created_by')

        project_id = self.request.query_params.get('project')
        status = self.request.query_params.get('status')
        assigned = self.request.query_params.get('assigned_to_me')

        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        if assigned == 'true':
            qs = qs.filter(assigned_to=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        task = self.get_object()
        if not request.user.is_admin and task.assigned_to != request.user:
            return Response(
                {'error': 'You can only update status of tasks assigned to you.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = TaskStatusUpdateSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TaskSerializer(task, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
