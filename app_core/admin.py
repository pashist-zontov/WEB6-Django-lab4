from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from .models import Request, Comment, History, AuditLog, UserSettings, CustomUser

# Переименование главной модели "Группы" на "Звания"
Group._meta.verbose_name = "Роль"
Group._meta.verbose_name_plural = "Роли"

# Переопределение модели Group
admin.site.unregister(Group)

@admin.register(Group)
class RoleAdmin(GroupAdmin):
    filter_horizontal = ('permissions',)
    list_display = ('name',)
    search_fields = ('name',)

# Решгистрация CustomUser как очередной модели
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'department', 'position', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'department', 'groups')
    search_fields = ('username', 'email', 'department', 'position')


    # Поля для редактирования уже существующего пользователя
    fieldsets = UserAdmin.fieldsets + (
        ('Корпоративная информация', {
            'fields': ('department', 'position')
        }),
    )

    # Поля для создания нового пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Корпоративная информация', {
            'fields': ('first_name', 'last_name', 'department', 'position', 'email')
        }),
    )

# Остальные модели
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('request', 'author', 'created_at')
    list_filter = ('created_at', 'author')

@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('request', 'user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'ip_address', 'method', 'path', 'status_code')
    list_filter = ('method', 'status_code', 'created_at')
    search_fields = ('path', 'ip_address', 'user__username')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'method', 'path', 'status_code', 'created_at')

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'email_notifs')