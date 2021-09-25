from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djongo import models

from apps.messenger.models import MemberModel


class Message(models.Model):
    _id = models.ObjectIdField()

    status = models.SmallIntegerField(verbose_name=_('message delivery status'), choices=settings.MESSAGE_STATUS,
                                      default=0)
    reply_to = models.JSONField(verbose_name=_('reply to message'))
    contents = models.TextField(verbose_name=_('message contents'), null=False, blank=False, editable=False)
    is_pinned = models.BooleanField(verbose_name=_('is pinned message'), default=False)
    seen_by = models.ArrayField(
        model_container=MemberModel,
        null=True,
        blank=True,
    )

    extras = models.JSONField(blank=True, null=True, default={})

    user_created = models.UUIDField(verbose_name=_('user created'), null=True, blank=True)
    date_created = models.DateTimeField(verbose_name=_('created date'), default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name=_('modified date'), default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        in_db = 'no_sql'
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


class MessageForm(forms.ModelForm):
    class Meta:
        models = Message
        fields = ('reply_to', 'contents', 'extras')


class Thread(models.Model):
    name = models.CharField(verbose_name=_('Thread name'), null=True, blank=True, max_length=120)
    icon = models.TextField(verbose_name=_('Link to thread icon'), null=True, blank=True)
    members = models.ArrayField(
        model_container=MemberModel,
        verbose_name=_('Members of the thread')
    )

    members_roles = models.JSONField(verbose_name=_('Member roles'), null=True, blank=True)
    messages = models.ArrayField(
        model_container=Message,
        model_form_class=MessageForm,
        verbose_name=_('Thread messages'),
        null=True,
        blank=True
    )
    is_encrypted = models.BooleanField(verbose_name=_('Is an encrypted thread'), default=False, editable=False)
    leader_id = models.ObjectIdField(verbose_name=_('Thread leader id'), null=True, blank=True)

    extras = models.JSONField(null=True, blank=True)

    user_created = models.UUIDField(verbose_name=_('user created'), null=True, blank=True)
    date_created = models.DateTimeField(verbose_name=_('created date'), default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name=_('modified date'), default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        in_db = 'no_sql'
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
