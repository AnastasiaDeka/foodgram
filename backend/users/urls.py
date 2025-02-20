from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('list/', views.UserListView.as_view(), name='user_list'),  # Для администраторов
]
