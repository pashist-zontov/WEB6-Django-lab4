from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Request, Comment, History
from .serializers import RequestSerializer, CommentSerializer
import logging

logger = logging.getLogger(__name__)

class WhatUserRole(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser: return True
        # Проверка на наличие группы "Модератор"
        if request.user.groups.filter(name='Модератор').exists(): return True
        return obj.owner == request.user


class RequestViewSet(viewsets.ModelViewSet):
    queryset = Request.objects.all().select_related('owner') # Множетсво данных о запросах с пользователями
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated, WhatUserRole]

    def perform_create(self, serializer):
        logger.info(f'Создание заявки пользователем {self.request.user.username}')
        
        instance = serializer.save(owner=self.request.user)

        # Запись в историю
        History.objects.create(
            request=instance,
            user=self.request.user,
            action='CREATE',
            details={
                'title': instance.title,
                'status': instance.status,
                'message': 'Заявка создана'
            }
        )
    
    # Упрощённая форма записи в модель History
    def perform_update(self, serializer):
        old_status = serializer.instance.status
        serializer.save()
        if old_status != serializer.instance.status:
            pass
    
