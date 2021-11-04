from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db import models
from jsonfield import JSONField

from apps.messenger.exceptions import PreKeyCountExceededError
from apps.messenger.utils import AuthenticationCredentials

UserModel = get_user_model()


class PreKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    public_key = models.TextField(verbose_name=_('public key'))
    device = models.ForeignKey('DeviceInfo', verbose_name=_('device pre key'), on_delete=models.CASCADE, null=True,
                               blank=True)

    # preKeyState = models.ForeignKey('PreKeyState', verbose_name=_('list pre keys'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Preparation Key')
        verbose_name_plural = _('Preparation Keys')
        default_permissions = ()

    @staticmethod
    def create(registration_id, user, *args, **kwargs):
        device_ref = DeviceInfo.objects.filter(user=user, registrationId=registration_id).get()
        if device_ref.prekey_set.count() > 99:
            raise PreKeyCountExceededError()
        return PreKey.create(*args, **kwargs)


class SignedPreKey(PreKey):
    signature = models.TextField(verbose_name=_('pre-key signature'))

    class Meta:
        verbose_name = _('Signed pre-key')
        verbose_name_plural = _('Signed pre-keys')
        default_permissions = ()


class DeviceInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(verbose_name=_('device name'), null=True, blank=True, max_length=100)
    user = models.ForeignKey(UserModel, verbose_name=_('device of user'), on_delete=models.CASCADE)

    token = models.TextField(verbose_name=_('auth token'), null=True, blank=True)
    salt = models.TextField(null=True, blank=True)

    gcm_id = models.TextField(null=True, blank=True)
    apn_id = models.TextField(null=True, blank=True)
    void_apn_id = models.TextField(null=True, blank=True)

    push_time_stamp = models.DateTimeField(default=timezone.now)
    fetches_messages = models.BooleanField(default=False)

    registration_id = models.UUIDField(null=True, blank=True)
    signed_pre_key = models.OneToOneField(
        to=SignedPreKey,
        verbose_name=_('signed preKey'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    last_seen = models.DateTimeField(verbose_name=_('last seen time'), default=timezone.now)
    created_date = models.DateField(verbose_name=_('session created date'), default=timezone.now, editable=False)

    class Meta:
        verbose_name = _('Device info')
        verbose_name_plural = _('Devices info')
        ordering = ('-created_date',)
        default_permissions = ()
        permissions = (
            ('view_all_device_info', _('Can view all device info')),
            ('view_device_info', _('Can view device info')),
            ('add_device_info', _('Can add device info')),
            ('change_all_device_info', _('Can change all device info')),
            ('change_device_info', _('Can change device info')),
            ('delete_all_device_info', _('Can delete all device info')),
            ('delete_device_info', _('Can delete device info'))
        )

    def is_enabled(self):
        has_channel = self.fetches_messages or self.apn_id or self.gcm_id
        return (self.id == settings.MASTER_ID and self.signed_pre_key is not None and has_channel) or (
                self.id != settings.MASTER_ID and has_channel and self.signed_pre_key is not None and (
                self.last_seen - timezone.now()) < 30)

    def is_master(self):
        return self.id == settings.MASTER_ID

    @staticmethod
    def get_enable_device_count(user):
        count = 0
        devices = DeviceInfo.objects.filter(user=user)
        for device in devices:
            if device.is_enable():
                count += 1
        return count

    @staticmethod
    def create_credentials(auth_token, salt=None):
        credentials = AuthenticationCredentials(auth_token, salt)
        return credentials.hashed_auth_token, credentials.salt

    @classmethod
    def create(cls, user, password, registration_id, fetches_messages=False, token=None, *args, **kwargs):
        auth_token, salt = cls.create_credentials(password)
        return DeviceInfo.objects.create(user=user, token=auth_token, salt=salt, registration_id=registration_id,
                                         fetches_messages=fetches_messages, *args, **kwargs)


class UserInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=True)
    user = models.ForeignKey(UserModel, verbose_name=_('user credentials'), on_delete=models.CASCADE)

    friend = models.ManyToManyField(
        UserModel,
        symmetrical=False,
        blank=True,
        verbose_name=_('user friends'),
        related_name='user_friends',
        related_query_name='user_info'
    )
    thread = models.TextField(verbose_name=_('user threads'), null=True, blank=True)

    extras = JSONField(default={})
    created_date = models.DateField(verbose_name=_('session created date'), default=timezone.now)

    class Meta:
        verbose_name = _('User\'s credential')
        verbose_name_plural = _('User\'s credentials')
        ordering = ('-created_date',)
        default_permissions = ()
        permissions = (
            ('view_all_credential', _('Can view all credential')),
            ('view_credential', _('Can view credential')),
            ('add_credential', _('Can add credential')),
            ('change_all_credential', _('Can change all credential')),
            ('change_credential', _('Can change credential')),
            ('delete_all_credential', _('Can delete all credential')),
            ('delete_credential', _('Can delete credential'))
        )
