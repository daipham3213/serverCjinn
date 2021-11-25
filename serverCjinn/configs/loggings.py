import os

from django.conf import settings

# logging
LOG_DIR = os.path.join(settings.BASE_DIR, 'logs')
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
        'filter_format': {
            'format': '[%(asctime)s] [%(count)s] [%(levelname)s] [API: %(api_name)s] [username: %(username)s] [count: %(count)s] SQL: %(message)s',
            'datefmt': "%d/%m/%Y-%H:%M:%S"
        },
        "rq_console": {
            "format": "%(asctime)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'api.log'),
            'when': 'D',
            'interval': 1,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'filter_log': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'filter.log'),
            'when': 'D',
            'interval': 1,
            'backupCount': 10,
            'formatter': 'filter_format',
        },
        "rq_console": {
            "level": "DEBUG",
            "class": "rq.utils.ColorizingStreamHandler",
            "formatter": "rq_console",
            "exclude": ["%(asctime)s"],
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
        },
        'filter': {
            'handlers': ['filter_log'],
            'level': 'INFO'
        },
        "rq.worker": {
            "handlers": ["rq_console", "sentry"],
            "level": "DEBUG"
        },
    },
}
