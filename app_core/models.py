from django.db import models
from django.contrib.auth.models import AbstractUser # Упрощённый подход к созданию класса аутентификации пользователя любого статуса
from django.conf import settings as stgs


"""МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ"""
class CustomUser(AbstractUser):
    # В абстрактном классе пользователя имеются базовые и некоторые дополнительные данные
    # Здесь мы добавляем новые поля для этой модели
    department = models.CharField(max_length=100, blank=True, verbose_name="Департамент/Отдел")
    position = models.CharField(max_length=100, blank=True, verbose_name="Должность")
    
    class Meta:
        db_table = "portal_User" # - смена на собственное имя таблицы
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f'[{self.position.upper()}] {self.username} ({self.department})'


"""МОДЕЛЬ ПОЛЬЗОВАТЕЛЬСКИХ НАСТРОЕК"""
class UserSettings(models.Model):
    user = models.OneToOneField(stgs.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="settings")
    theme = models.CharField(max_length=20, choices=[('light', 'Светлая'), ('dark', 'Тёмная')], default='light')
    email_notifs = models.BooleanField(db_default=True)

    def __str__(self):
        return f'Настройки пользователя {self.user.username} [{self.user.pk}]'

    class Meta:
        verbose_name_plural = "Найстройки пользователей"

"""МОДЕЛЬ ПЕРЕДАЧИ ЗАЯВОК"""
class Request(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новая'),
        ('IN_PROGRESS', 'В процессе'),
        ('FINISHED', 'Обработана'),
        ('CLOSED', 'Закрыта')
    ]

    title = models.CharField(max_length=255, verbose_name="Тема заявки")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    owner = models.ForeignKey(stgs.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests')
    # Файлы группируются по годам и месяцам для гибкости файловой системы
    file = models.FileField(upload_to='requests/%Y/%m/', blank=True, null=True, verbose_name="Прикрепляемый файл")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f'Заявка #{self.id}: {self.title}'


"""МОДЕЛЬ КОММЕНТАРИЕВ"""
class Comment(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(stgs.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комметарии модераторов"


"""МОДЕЛЬ ОТОБРАЖЕНИЯ ИСТОРИИ В ЧИТАЕМОМ ВИДЕ (для всех пользователей)"""
class History(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(stgs.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50) # Передаваемая информация действия из неопределённого набора
    details = models.JSONField(default=dict) # Составление деталей через автоматизацию, добавляющую свои параметры
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История"
        verbose_name_plural = "Истории"


"""МОДЕЛЬ ЖУРНАЛА АУДИТА (для админов)"""
class AuditLog(models.Model):
    user = models.ForeignKey(stgs.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField() # Специфичный CharField с проверкой на корректность IP-адреса
    user_agent = models.TextField(blank=True) # Идентификация клиента по используемому браузеру. Длина текста может быть длинее 255 символов
    method = models.CharField(max_length=10) # GET, POST, PUT, DELETE или PATCH
    status_code = models.IntegerField() # Кодовое значение статуса выполнения HTTP-запроса
    path = models.TextField() # Путь запроса
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Лог"
        verbose_name_plural = "Журнал аудита"