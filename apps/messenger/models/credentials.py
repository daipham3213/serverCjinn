from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djongo import models


class MemberModel(models.Model):
    _id = models.ObjectIdField()
    user_id = models.UUIDField(verbose_name=_('Member id'))
    joined_date = models.DateTimeField(verbose_name=_('member joined date'), default=timezone.now, editable=False)
    is_blocked = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        in_db = 'no_sql'
        verbose_name = _('Member')
        verbose_name_plural = _('Members')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = (
            ('view_all_member', _('Can view all member')),
            ('view_member', _('Can view member')),
            ('add_member', _('Can add member')),
            ('change_all_member', _('Can change all member')),
            ('change_member', _('Can change member')),
            ('delete_all_member', _('Can delete all member')),
            ('delete_member', _('Can delete member'))
        )


class UserThread(models.Model):
    _id = models.ObjectIdField()
    status = models.SmallIntegerField(verbose_name=_('Thread status'), choices=settings.THREAD_STATUS, default=0)
    joined_date = models.DateField(verbose_name=_('Thread joined date'), default=timezone.now, editable=False)
    is_muted = models.BooleanField(verbose_name=_('mute thread'), default=False)

    extras = models.JSONField(default={})

    class Meta:
        in_db = 'no_sql'
        verbose_name = _('User\'s thread')
        verbose_name_plural = _('User\'s threads')
        ordering = _('-joined_date',)
        default_permissions = ()
        permissions = (
            ('view_all_user_thread', _('Can view all user_thread')),
            ('view_user_thread', _('Can view user_thread')),
            ('add_user_thread', _('Can add user_thread')),
            ('change_all_user_thread', _('Can change all user_thread')),
            ('change_user_thread', _('Can change user_thread')),
            ('delete_all_user_thread', _('Can delete all user_thread')),
            ('delete_user_thread', _('Can delete user_thread'))
        )


class Session(models.Model):
    _id = models.ObjectIdField()
    device = models.CharField(verbose_name=_('device name'), null=True, blank=True, max_length=150)
    public_key = models.TextField(verbose_name=_('device public key'))
    status = models.SmallIntegerField(verbose_name=_('session status'), default=0)
    is_deleted = models.BooleanField(default=False)
    is_share_location = models.BooleanField(default=False)
    location = models.JSONField(default={}, verbose_name=_('device location'))

    token = models.TextField(verbose_name=_('token'), null=True, blank=True)

    extras = models.JSONField(default={})

    class Meta:
        in_db = 'no_sql'
        verbose_name = _('User\'s session')
        verbose_name_plural = _('User\'s sessions')
        ordering = _('-joined_date', )
        default_permissions = ()
        permissions = (
            ('view_all_user_session', _('Can view all user_session')),
            ('view_user_session', _('Can view user_session')),
            ('add_user_session', _('Can add user_session')),
            ('change_all_user_session', _('Can change all user_session')),
            ('change_user_session', _('Can change user_session')),
            ('delete_all_user_session', _('Can delete all user_session')),
            ('delete_user_session', _('Can delete user_session'))
        )

    @classmethod
    def create_session(cls, token=None):


class Credential(models.Model):
    _id = models.ObjectIdField(verbose_name='credential id')
    user = models.ForeignKey(get_user_model(), verbose_name=_('user credentials'), on_delete=models.CASCADE)
    threads = models.ArrayField(
        model_container=UserThread,
        null=True,
        blank=True
    )
    friends = models.ArrayField(
        model_container=MemberModel,
        null=True,
        blank=True,
    )
    sessions = models.ArrayField(
        model_container=Session,
        null=True,
        blank=True
    )

    extras = models.JSONField(default={})

    class Meta:
        in_db = 'no_sql'
        verbose_name = _('User\'s credential')
        verbose_name_plural = _('User\'s credentials')
        ordering = _('-joined_date', )
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

    @classmethod
    def get_or_create(cls, user=None, token=None, extras={}):