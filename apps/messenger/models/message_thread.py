from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db import models
from jsonfield import JSONField

from apps.messenger.models import UserInfo


class MemberInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(UserInfo, verbose_name=_('member info'), on_delete=models.CASCADE)

    joined_date = models.DateTimeField(verbose_name=_('member joined date'), default=timezone.now, editable=False)
    is_blocked = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Member')
        verbose_name_plural = _('Members')
        ordering = ('-joined_date',)
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


class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    name = models.CharField(verbose_name=_('Thread name'), null=True, blank=True, max_length=120)
    icon = models.TextField(verbose_name=_('Link to thread icon'), null=True, blank=True)
    members = models.ManyToManyField(MemberInfo, verbose_name=_('Members of the thread'), )

    members_roles = models.JSONField(verbose_name=_('Member roles'), null=True, blank=True)

    is_encrypted = models.BooleanField(verbose_name=_('Is an encrypted thread'), default=False, editable=False)
    leader_id = models.UUIDField(verbose_name=_('Thread leader id'), null=False, blank=False)

    extras = models.JSONField(null=True, blank=True, default={})

    user_created = models.UUIDField(verbose_name=_('user created'), null=True, blank=True)
    date_created = models.DateTimeField(verbose_name=_('created date'), default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name=_('modified date'), default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Message thread')
        verbose_name_plural = _('Message threads')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = (
            ('view_all_thread', _('Can view all thread')),
            ('view_thread', _('Can view thread')),
            ('add_thread', _('Can add thread')),
            ('change_all_thread', _('Can change all thread')),
            ('change_thread', _('Can change thread')),
            ('delete_all_thread', _('Can delete all thread')),
            ('delete_thread', _('Can delete thread'))
        )

    def __str__(self):
        return '{} - {}'.format(self.name, self.date_created)


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    thread = models.ForeignKey(Thread, verbose_name=_('thread of message'), on_delete=models.CASCADE)
    status = models.SmallIntegerField(verbose_name=_('message delivery status'), choices=settings.MESSAGE_STATUS,
                                      default=0)
    reply_to = models.ForeignKey('self', verbose_name=_('reply to message'), on_delete=models.DO_NOTHING)
    contents = models.TextField(verbose_name=_('message contents'), null=False, blank=False, editable=False)
    is_pinned = models.BooleanField(verbose_name=_('is pinned message'), default=False)

    extras = JSONField(blank=True, null=True, default={})
    user_created = models.UUIDField(verbose_name=_('user created'), null=True, blank=True)
    date_created = models.DateTimeField(verbose_name=_('created date'), default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name=_('modified date'), default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Message')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = (
            ('view_all_message', _('Can view all message')),
            ('view_message', _('Can view message')),
            ('add_message', _('Can add message')),
            ('change_all_message', _('Can change all message')),
            ('change_message', _('Can change message')),
            ('delete_all_message', _('Can delete all message')),
            ('delete_message', _('Can delete message'))
        )

    def __str__(self):
        return '{} - {}'.format(self.date_created, self.status)
