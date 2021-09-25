import os
from pathlib import Path

from django.utils.translation import ugettext_lazy as _
import django_opentracing
from django_filters import rest_framework as filters

# Build paths inside the project like this: BASE_DIR / 'subdir'.

import sys
import django.db.models.options as options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)
sys.setrecursionlimit(10000)

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4b_6g*ebq8%4u2=zx7o6xy=0j^a3f6(xzsi+azv#nz#71946x+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'django_filters',
    'djongo',
    'apps.base',
    'apps.auths',
    'apps.account',
    'apps.log',
    'apps.messenger'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.base.middleware.CjinnMiddleware',
    'apps.base.middleware.OnlineNowMiddleware',
    'django_opentracing.OpenTracingMiddleware',
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

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'railway',
        'USER': 'root',
        'PASSWORD': 'MvMvdAgS9Zdw2TkE5b49',
        'HOST': 'containers-us-west-11.railway.app',
        'PORT': '5856'
    },
    'no_sql': {
        'ENGINE': 'djongo',
        'NAME': 'db-mda',
        'CLIENT': {
            'host': 'localhost:27017',
        }
    }
}

DATABASE_ROUTERS = ['apps.db_routers.DBRouter', 'apps.db_routers.NOSQLRouter']

#  MONGO DB connection\
# _MONGODB_USER = ""
# _MONGODB_PASSWD = ""
# _MONGODB_HOST = "localhost"
# _MONGODB_NAME = "db-mda"
# _MONGODB_PORT = 27017
# _MONGODB_DATABASE_HOST = "mongodb://%s:%s@%s/%s" % (
#     _MONGODB_USER,
#     _MONGODB_PASSWD,
#     _MONGODB_HOST,
#     _MONGODB_NAME,
# )
#
# mongoengine.connect(_MONGODB_NAME, host=_MONGODB_HOST, port=_MONGODB_PORT)
#
GRAPHENE = {"SCHEMA": "apps.base.schema.schema"}

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

try:
    from .local_settings import *
except (ImportError, Exception) as e:
    print(e)
