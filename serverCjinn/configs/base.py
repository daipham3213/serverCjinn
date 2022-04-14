from django.utils.translation import ugettext_lazy as _

KEY_VIEW_TOKEN = "c59132e3de6a4460a4d84b344371201d"

# mail
DEFAULT_IS_OWNER_MAIL = False
DEFAULT_HOST = None
DEFAULT_PORT = None
DEFAULT_USERNAME_MAIL = None
DEFAULT_PASSWORD_MAIL = None
DEFAULT_REPLY_MAIL = 'api.projectmng@gmail.com'
DEFAULT_FROM_MAIL = 'no-reply@gmail.com'
DEFAULT_PREFIX_MAIL = '[Cjinn] Notification'
DEFAULT_CC_MAIL = []
DEFAULT_BCC_MAIL = []

DEFAULT_THEME = 2
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'
DEFAULT_LANGUAGE = 'vi'
DEFAULT_CURRENCY_CODE = 'VND'
DEFAULT_INHERITOR = 0
CONFIG_SYNC = [
    'inheritor', 'generator',
    'allow_mail_notify', 'template_mail',
    'allow_print', 'template_print'
]
DEFAULT_PASSWORD = None

LANGUAGE_CHOICE = (
    ('vi', _('Vietnamese')),
    ('en', _('English'))
)

ROLE_GROUP_REF_TYPE = (
    ('department', _('Department')),
    ('job_position', _('Job Position')),
    ('position_type', _('Position Type'))
)

STATUS = (
    (0, _('Initial approval')),
    (1, _('Proceeding approval')),
    (2, _('Approved approval')),
    (3, _('Rejected approval')),
    (4, _('Added')),
    (5, _('Canceled')),
    (6, _('Finish')),

    (10, _('Initial info')),
    (11, _('Proceeding info')),
    (12, _('Approved info')),
    (13, _('Rejected info')),

    (20, _('Final complete '))
)
