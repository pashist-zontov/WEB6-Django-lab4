import uuid
import time
from contextvars import ContextVar
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
import datetime
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.cache import cache
import logging


request_id_var: ContextVar[str] = ContextVar('request_id', default='no-request-id') # Тарабарщина. Разобраться бы.

"""КЛАСС СБОРА ИНФОРМАЦИИ О ЗАПРОСЕ В request_id"""
class RequestIDMiddleware:
    def __init__(self, get_resp):
        self.get_response = get_resp
    
    def __call__(self, request):
        req_id = str(uuid.uuid4())
        request.request_id = req_id
        token = request_id_var.set(req_id)
    
        try:
            response = self.get_response(request) # Разделение между входящей информацией и исходящей
            response['X-Request-ID'] = req_id
            return response
        finally:
            request_id_var.reset(token) # Предотвращение утечки данных в случае успеха или ошибки


"""ФИЛЬТРАЦИЯ request_id ДЛЯ ЗАПИСИ В ЛОГИ"""
class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


"""КЛАСС АУДИТА ДЕЙСТВИЙ ПОЛЬЗОВАТЕЛЯ"""
class AuditMiddleware:
    def __init__(self, get_resp):
        self.get_response = get_resp
    
    def __call__(self, request):
        response = self.get_response(request)

        # Игнор проверок на работоспособность и статических файлов
        if request.path.startswith(('/static/', '/media/', '/health')):
            return response
        
        from .models import AuditLog
        
        # Откладка получения ответа клиентом, чтобы сначала записать всё в БД
        transaction.on_commit(lambda: AuditLog.objects.create(
            user = request.user if request.user.is_authenticated else None,
            ip_address = request.META.get('REMOTE_ADDR', 'unknown'),
            user_agent = request.META.get('HTTP_USER_AGENT', ''),
            method = request.method,
            status_code = response.status_code,
            path = request.path
        ))
        return response


"""ОГРАНИЧИТЕЛЬ ЧАСТОТЫ ЗАПРОСОВ"""
class RateLimitMiddleware:
    def __init__(self, get_resp):
        self.get_response = get_resp
        self.limit = 60 # Ограничение числа запросов
        self.window = 60 # Ограничение в секундах
    
    def __call__(self, request):
        if request.path.startswith('/api/'):
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            key = f'rate_limit_{ip}'

            now = time.time()
            history = cache.get(key, [])
            # Проверка на количество и частоту запросов одновременно проходит через хранение во "временном окне"
            history = [t for t in history if (now - t < self.window)]
            if len(history) >= self.limit:
                return HttpResponse('Исчерпан лимит запросов', 429)
            
            history.append(now)
            cache.set(key, history, self.window)
        
        return self.get_response(request)


"""АВТО-ОПРЕДЕЛИТЕЛЬ ПОЛЬЗОВАТЕЛЯ"""
class AutoUserMiddleware:
    def __init__(self, get_resp):
        self.get_response = get_resp
    
    def __call__(self, request):
        # Проверка в первую очередь проходит через получение информации о ранее выполненной аутентификации пользователем
        if not request.user.is_authenticated:
            # Попытка определить через заголовок прокси
            user_id = request.META.get('HTTP_USER_ID') or request.META.get('HTTP_REMOTE_USER')
            if user_id:
                try:
                    # Поиск по авто-созданному id
                    User = get_user_model()
                    request.user = User.objects.get(id=user_id)
                    request._cached_user = request.user
                except:
                    # Если найден не был, определяем пользователя как не авторизованного
                    pass

        return self.get_response(request)


"""ЗАПРЕТ НА ВЫПОЛЕНИЕ ОПЕРАЦИЙ В НЕ РАБОЧЕЕ ВРЕМЯ"""
class WorkingHoursMiddleware:
    def __init__(self, get_resp):
        self.get_response = get_resp
    
    def __call__(self, request):
        # Булево значение, обозначающее "опасность" операции (как, например, изменение, удаление данных)
        is_dangerous = request.method in ['DELETE', 'PUT', 'PATCH'] or '/admin/' in request.path # Я фигею, насколько это гениально

        if is_dangerous and request.user.is_authenticated and (not request.user.is_superuser): # !!!
            now = timezone.localtime(timezone.now())

            # Установленное человеческое рабочее время: Пн-Сб (0-5), С 12:00 до 16:30
            start_work = datetime.time(12, 0, 0)
            end_work = datetime.time(16, 30, 0)
            is_working_hours = now.weekday() < 6 and (start_work <= now.time() <= end_work)

            if not is_working_hours:
                return HttpResponseForbidden(
                    "ДОСТУП ЗАПРЕЩЁН: Изменение данных вне рабочего времени (ПН-СБ, 12:00-16:30) "
                    "доступно только администраторам. Позвоните нам по номеру - 8 (800) 555-35-35"
                )
        
        return self.get_response(request)