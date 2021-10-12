from django.conf import settings
import os
from jaeger_client import Config
import django_opentracing

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db-mda',
        'USER': 'root',
        'PASSWORD': '123456@abc',
        'HOST': '127.0.0.1',
        'PORT': '3306'
    },
}

# logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y-%H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(settings.LOG_DIR, 'api.log'),
            'when': 'D',
            'interval': 1,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'root': {
            'handlers': ['file'],
            'level': 'ERROR',
        }
    },
}

SHOW_API_DOC = True
API_CACHES_TIME = 0

# jaeger tracer
OPENTRACING_TRACE_ALL = True
config = Config(
    config={
        'sampler': {
            'type': 'const',
            'param': 1,
        },
        'local_agent': {
            'reporting_host': 'localhost',
            'reporting_port': '6831',
        },
        'logging': True
    },
    service_name='CJINN-APP',
    validate=True,
)
tracer = config.initialize_tracer()
OPENTRACING_TRACING = django_opentracing.DjangoTracing(tracer)
