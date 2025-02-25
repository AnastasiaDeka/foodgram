from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
]
