from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.messenger.exceptions import PreKeyCountExceededError
from apps.messenger.func import get_user_cache
from apps.messenger.utils import AuthenticationCredentials

UserModel = get_user_model()


class PreKey(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    public_key = models.TextField(verbose_name=_('public key'))
    device = models.ForeignKey('DeviceInfo', verbose_name=_('device pre key'), on_delete=models.CASCADE, null=True,
                               blank=True)

    # preKeyState = models.ForeignKey('PreKeyState', verbose_name=_('list pre keys'), on_delete=models.CASCADE)

    class Meta:
        unique_together = (('id', 'device_id'),)
        verbose_name = _('Preparation Key')
        verbose_name_plural = _('Preparation Keys')
        default_permissions = ()

    @staticmethod
    def create(registration_id, user, *args, **kwargs):
        device_ref = DeviceInfo.objects.filter(user=user, registrationId=registration_id, *args, **kwargs).get()
        if device_ref.prekey_set.count() > 99:
            raise PreKeyCountExceededError()
        return PreKey.create(*args, **kwargs)


class SignedPreKey(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    public_key = models.TextField(verbose_name=_('public key'))
    signature = models.TextField(verbose_name=_('pre-key signature'))

    class Meta:
        verbose_name = _('Signed pre-key')
        verbose_name_plural = _('Signed pre-keys')
        default_permissions = ()


class DeviceInfo(models.Model):
    id = models.UUIDField(verbose_name=_('device_id'), default=uuid4, primary_key=True)
    name = models.CharField(verbose_name=_('device name'), null=True, blank=True, max_length=100)
    user = models.ForeignKey(UserModel, verbose_name=_('device of user'), on_delete=models.CASCADE)

    token = models.TextField(verbose_name=_('auth token'), null=True, blank=True)
    salt = models.TextField(null=True, blank=True)

    gcm_id = models.TextField(null=True, blank=True)
    apn_id = models.TextField(null=True, blank=True)
    void_apn_id = models.TextField(null=True, blank=True)

    push_time_stamp = models.DateTimeField(default=timezone.now)
    fetches_messages = models.BooleanField(default=False)

    registration_id = models.PositiveIntegerField(verbose_name=_('registration id'))
    signed_pre_key = models.OneToOneField(
        to=SignedPreKey,
        verbose_name=_('signed preKey'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_stale = models.BooleanField(default=True)
    is_master = models.BooleanField(default=False)

    last_seen = models.DateTimeField(verbose_name=_('last seen time'), default=timezone.now)
    created_date = models.DateField(verbose_name=_('session created date'), default=timezone.now, editable=False)

    class Meta:
        unique_together = (('registration_id', 'user_id'),)
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
        return (self.is_master and self.signed_pre_key is not None and has_channel) or (
                not self.is_master and has_channel and self.signed_pre_key is not None and (
                self.last_seen - timezone.now()) < 30)

    @classmethod
    def check_device_availability(cls, device):
        if not device.apn_id and not device.gcm_id and not get_user_cache(device.user_id):
            raise Exception('Unable to communicate with receiver')
        method = ''
        user_cache = get_user_cache(device.user_id)
        if user_cache:
            dev = user_cache.find_device(str(device.id))
            if dev and dev.incoming_msg:
                method = 'websocket'
            else:
                device.fetches_messages = False
                device.save()
        if method != '':
            return method
        elif device.gcm_id:
            method = 'gcm'
        elif device.apn_id:
            method = 'apn'

        return method

    @staticmethod
    def get_enable_device_count(user):
        count = 0
        devices = DeviceInfo.objects.filter(user=user)
        for device in devices:
            if device.is_enabled():
                count += 1
        return count

    @staticmethod
    def create_credentials(auth_token, salt=None):
        credentials = AuthenticationCredentials(auth_token, salt)
        return credentials.hashed_auth_token, credentials.salt

    @classmethod
    def create(cls, user, password, registration_id, fetches_messages=False, token=None, *args, **kwargs):
        auth_token, salt = cls.create_credentials(password)
        has_device = DeviceInfo.objects.filter(user=user).count()
        return DeviceInfo.objects.create(user=user, token=auth_token, salt=salt, registration_id=registration_id,
                                         fetches_messages=fetches_messages, is_master=has_device == 0, *args, **kwargs)


class UserInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(UserModel, verbose_name=_('user credentials'), on_delete=models.CASCADE)
    contacts = models.TextField(verbose_name=_('user contacts'), null=True, blank=True, default='')
    threads = models.ManyToManyField(
        'Thread',
        through='MemberInfo',
        verbose_name=_('user threads'),
        blank=True,
        symmetrical=False,
    )

    extras = models.JSONField(default=dict)
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

    def get_friend_requests(self):
        requests = self.extras.get('friend_request', {})
        return requests

    def send_friend_request(self, user_id):
        # init friend request data
        friend = UserInfo.objects.get(user_id=user_id)
        if friend.extras.get('friend_request', None) is None:
            friend.extras['friend_request'] = {}
        if self.extras.get('friend_request', None) is None:
            self.extras['friend_request'] = {}
        # check if user_id in contact
        if self.contacts and self.contacts.__contains__(user_id):
            raise Exception(_('User already in contact list'))
        if self.user_id.__str__() == user_id:
            raise Exception(_('Invalid request'))

        if friend and self:
            timestamp = timezone.now()
            # create request
            if friend.extras['friend_request'].get(self.user_id.__str__(), None) is None:
                # limit friend request
                if friend.extras['friend_request'].keys().__len__() > settings.FRIEND_REQUEST_LIMIT:
                    raise Exception(_('Friend request limit exceed'))

                friend.extras['friend_request'][self.user_id.__str__()] = {
                    'timestamp': timestamp.__str__(),
                    'type': 'receiver'
                }
                self.extras['friend_request'][friend.user_id.__str__()] = {
                    'timestamp': timestamp.__str__(),
                    'type': 'sender'
                }
                self.save()
                friend.save()
            else:
                raise Exception(_('Friend request already sent.'))
        else:
            raise Exception(_('Invalid input'))
        return True

    def process_friend_request(self, user_id, is_accept=True):
        if isinstance(self.extras, dict) and self.extras.get('friend_request', None):
            if self.extras['friend_request'].get(user_id, None) \
                    and self.extras['friend_request'][user_id]['type'] == 'receiver':
                # process request
                sender = UserInfo.objects.get(user_id=user_id)
                if is_accept:
                    if not isinstance(sender.contacts, str):
                        sender.contacts = ''
                    if not isinstance(self.contacts, str):
                        self.contacts = ''
                    self.contacts = user_id.__str__() + '|' + self.contacts
                    sender.contacts = self.user_id.__str__() + '|' + sender.contacts
                self.extras['friend_request'].pop(user_id)
                sender.extras['friend_request'].pop(self.user_id.__str__())
                self.save()
                sender.save()
                return True
            else:
                raise Exception(_('Invalid add friend request'))
        raise Exception(_('Invalid input'))

    def remove_contact(self, user_id):
        contact_list = self.get_contacts()
        try:
            owner_id = self.user_id
            contact_list.remove(user_id)
            self.contacts = '|'.join(contact_list)
            self.save()

            # remove from other user
            other = UserInfo.objects.filter(user_id=user_id).first()
            contact_list = other.get_contacts()
            contact_list.remove(owner_id)
            other.contacts = '|'.join(contact_list)
            other.save()
        except ValueError:
            return False
        return True

    def get_contacts(self):
        return ' '.join(self.contacts.split('|')).split()

    def get_threads(self):
        return self.threads.filter(memberinfo__is_blocked=False)

    def get_user(self):
        return UserModel.objects.filter(id=self.user_id).first()
