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

MASTER_ID = '1cd139bb-4d8e-4ccf-b12e-afaa2f814d55'

FRIEND_REQUEST_LIMIT = 100

CLIENTS_LIMIT = 100

MESSAGE_QUEUE_LIMIT = 100
