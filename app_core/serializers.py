"""ВАЛИДАЦИЯ ДАННЫХ СО СТОРОНЫ СЕРВЕРА <api.py>"""
from rest_framework import serializers
from .models import Request, Comment, CustomUser


class CommentSerializer(serializers.ModelSerializer):
    # Имя пользователя, написавшего комментарий. Только для чтения
    author_name = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'text', 'author_name', 'created_at']
        read_only_fields = ['author', 'created_at']


class RequestSerializer:
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    # Подсчёт комментариев к заявке
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = [
            'id', 'title', 'description', 'status', 'file',
            'owner_name', 'comments_count',
            'created_at', 'updated_at'
        ]

        read_only_fields = ['owner', 'created_at', 'updated_at']
    

    def get_comments_count(self, obj):
        return obj.comments.count()
    
    # Кастомная фукнция с валидацией данных перед сохранением
    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in Request.STATUS_CHOICES]
        if not (value in valid_statuses):
            raise serializers.ValidationError("НЕДОПУСТИСЫЙ СТАТУС ЗАЯВКИ")
        
        # Запрет на закрытие заявки без переданного описания
        if value == 'CLOSED' and (not self.instance.description):
            raise serializers.ValidationError("В ЗАКРЫВАЕМОЙ ЗАЯВКЕ ОТСУТСТВУЕТ ОПИСАНИЕ")
        
        return value
