from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Панель администратора
    path('api/', include('api.urls')),  # API-маршруты
]

