import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', get_random_secret_key())

DEBUG = os.getenv('DEBUG', 'False') == 'True'

#ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

ALLOWED_HOSTS = ['localhost', '127.0.0.1',]


CSRF_TRUSTED_ORIGINS = [
    'https://aderline.ru',
    'https://158.160.75.171'
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'recipes.apps.RecipesConfig',
    'users.apps.UsersConfig',
    'tags.apps.TagsConfig',
    'api.apps.ApiConfig',
    'djoser',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / "db.sqlite3",
       }
   }


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_ROOT = "/backend_static"
STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.PaginatorWithLimit',
    'PAGE_SIZE': 6,
}


DJOSER = {
    'LOGIN_FIELD': 'email',
    'HIDE_USERS': False,
    'SERIALIZERS': {
        'user_create': 'djoser.serializers.UserCreateSerializer',
        'user': 'api.serializers.UserSerializer',
        'current_user': 'api.serializers.UserSerializer',
    },
    'PERMISSIONS': {
        'user_create': ['rest_framework.permissions.AllowAny'],
        'user': ['rest_framework.permissions.AllowAny'],
        'user_list': ['rest_framework.permissions.AllowAny'],
    },
}
