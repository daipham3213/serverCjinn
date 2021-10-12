from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db import models
from jsonfield import JSONField

from apps.messenger.models.key import SignedPreKey

UserModel = get_user_model()


class DeviceInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(verbose_name=_('device name'), null=True, blank=True, max_length=100)
    user = models.ForeignKey(UserModel, verbose_name=_('device of user'), on_delete=models.CASCADE)

    token = models.TextField(verbose_name=_('auth token'), null=True, blank=True)
    salt = models.TextField(null=True, blank=True)

    gcmId = models.TextField(null=True, blank=True)
    apnId = models.TextField(null=True, blank=True)
    voidApnId = models.TextField(null=True, blank=True)

    pushTimeStamp = models.DateTimeField(default=timezone.now)
    fetchesMessages = models.BooleanField(default=False)

    registrationId = models.UUIDField(null=True, blank=True)
    signedPreKey = models.OneToOneField(
        to=SignedPreKey,
        verbose_name=_('signed preKey'),
        on_delete=models.DO_NOTHING
    )

    last_seen = models.DateTimeField(verbose_name=_('last seen time'), default=timezone.now)
    created_date = models.DateField(verbose_name=_('session created date'), default=timezone.now)

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
        has_channel = self.fetchesMessages or self.apnId or self.gcmId
        return (self.id == settings.MASTER_ID and self.signedPreKey is not None and has_channel) or (
                self.id != settings.MASTER_ID and has_channel and self.signedPreKey is not None and (
                self.last_seen - timezone.now()) < 30)

    def is_master(self):
        return self.id == settings.MASTER_ID


class UserInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=True)
    user = models.ForeignKey(UserModel, verbose_name=_('user credentials'), on_delete=models.CASCADE)

    friend = models.ManyToManyField(UserModel, verbose_name=_('user friends'), null=True, blank=True, related_name='user_friends')
    thread = models.ManyToManyField(UserModel, verbose_name=_('user threads'), null=True, blank=True, related_name='user_threads')

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
