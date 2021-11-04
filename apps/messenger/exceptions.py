from django.utils.translation import gettext as _


class MessengerError(Exception):
    default_message = None

    def __init__(self, message=None):
        if message is None:
            message = self.default_message

        super().__init__(message)


class PreKeyBundleError(MessengerError):
    default_message = _('Pre-Key bundle error')


class PreKeyCountExceededError(MessengerError):
    default_message = _('Pre key count exceed')


class SignedPreKeyInvalid(MessengerError):
    default_message = _('Invalid signed pre key format')


class DeviceLimitExceed(MessengerError):
    default_message = _('Too many active devices')
