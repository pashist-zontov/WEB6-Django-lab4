from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .api import RequestViewSet

# Роутер REST API
router = DefaultRouter()
router.register(r'requests', RequestViewSet, basename='api-request')


urlpatterns = [
    # Основа
    path('', views.request_list, name='request_list'),
    path('create/', views.request_create, name='request_create'),
    path('<int:pk>/', views.request_detail, name='request_detail'),
    path('<int:pk>/edit', views.request_edit, name='request_edit'),

    # Панель модератора
    path('mod/', views.mod_panel, name='mod_panel'),
    path('mod/<int:pk>/change-status/', views.change_status, name='change_status'),

    # API
    path('api/', include(router.urls))
]