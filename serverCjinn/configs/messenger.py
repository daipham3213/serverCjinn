from django.utils.translation import ugettext_lazy as _

MESSAGE_STATUS = (
    (0, _('Sending.')),
    (1, _('Delivered.')),
    (2, _('Notified.')),
    (3, _('Error!'))
)

THREAD_STATUS = (
    (0, _('Normal')),
    (1, _('High')),
    (2, _('Archive'))
)

DEVICE_LIMIT = 3

MASTER_ID = '1'

FRIEND_REQUEST_LIMIT = 100

CLIENTS_LIMIT = 100

MESSAGE_QUEUE_LIMIT = 100
