import os
import sys
from pathlib import Path

import django.db.models.options as options
from django.utils.translation import ugettext_lazy as _
from django_filters import rest_framework as filters
from firebase_admin import initialize_app, credentials

# Build paths inside the project like this: BASE_DIR / 'subdir'.

sys.setrecursionlimit(10000)

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = int(os.environ.get("DEBUG", default=0))

# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'fcm_django',
    'corsheaders',
    'graphene_django',
    'django_filters',
    'cloudinary',
    'django_rq',
    'channels',
    'apps.base',
    'apps.auths',
    'apps.account',
    'apps.log',
    'apps.messenger.apps.MessengerConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.base.middleware.CjinnMiddleware',
    'apps.base.middleware.OnlineNowMiddleware',
]

ROOT_URLCONF = 'serverCjinn.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'serverCjinn.wsgi.application'
ASGI_APPLICATION = 'serverCjinn.router.application'

CORS_ALLOWED_ORIGINS = ['http://127.0.0.1', 'http://192.168.1.10', 'http://192.168.1.9']
CORS_ALLOW_METHODS = [
    "OPTIONS",
    "PATCH",
    "POST",
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        }
    }
}

RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
    },
}

CACHE_TIMEOUT = 10 * 60 * 1000  # 10 MIN

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_DATABASE', 'db-mda'),
        'OPTIONS': {
            'options': '-c search_path=public'
        },
        'USER': os.environ.get('DB_USERNAME', 'admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '123456@abc'),
        'HOST': 'db',
        'PORT': '5432'
    },
}

FIREBASE_APP = initialize_app(credentials.Certificate(os.path.join(BASE_DIR, 'data/firebase-adminsdk.json')))
FCM_DJANGO_SETTINGS = {
    # default: _('FCM Django')
    "APP_VERBOSE_NAME": "[DEFAULT]",
    # true if you want to have only one active device per registered user at a time
    # default: False
    "ONE_DEVICE_PER_USER": False,
    # devices to which notifications cannot be sent,
    # are deleted upon receiving error response from FCM
    # default: False
    "DELETE_INACTIVE_DEVICES": True,
}

# WEBSOCKET_PATH = r'^graphql(?:/(?P<token>\w+|))(?:/(?P<device_id>[-\w]+))?/?'
WEBSOCKET_PATH = 'graphql'
GRAPHENE = {
    "SCHEMA": "apps.base.schema.schema",
    "SUBSCRIPTION_PATH": '/' + WEBSOCKET_PATH + '/',
    "DJANGO_CHOICE_FIELD_ENUM_V3_NAMING": True,
    "GRAPHIQL_HEADER_EDITOR_ENABLED": True,
    "SCHEMA_OUTPUT": "data/schema.json",
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'account.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.base.authentication.TokenAuthentication',
    'apps.auths.backends.account_backend.AccountBackend',
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'statics'),
)

PROJECT_NAME = 'Cjinn - Message App'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# others settings
LOG_DIR = os.path.join(BASE_DIR, 'logs')

try:
    from .configs import *
except Exception as e:
    print(e)

# try:
#     from .local_settings import *
# except (ImportError, Exception) as e:
#     print(e)

# if DEBUG:
#     for queueConfig in RQ_QUEUES.values():
#         queueConfig['ASYNC'] = False


import cloudinary

cloudinary.config(
    cloud_name="projectmngapi",
    api_key="296254975766871",
    api_secret="AkZ4OUJQbyyn0NcgiM92D9TbppI"
)
