from uuid import uuid4

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
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

    @classmethod
    def verify_user_id(cls, user_id):
        user = cls.user.objects.get(user_id=user_id)
        if user:
            return user
        return None


class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    name = models.CharField(verbose_name=_('Thread name'), null=True, blank=True, max_length=120)
    icon = models.TextField(verbose_name=_('Link to thread icon'), null=True, blank=True)
    members = models.ManyToManyField(MemberInfo, verbose_name=_('Members of the thread'))

    members_roles = models.JSONField(verbose_name=_('Member roles'), null=True, blank=True)

    is_encrypted = models.BooleanField(verbose_name=_('Is an encrypted thread'), default=False, editable=False)
    leader_id = models.UUIDField(verbose_name=_('Thread leader id'), null=False, blank=False)

    extras = models.JSONField(null=True, blank=True, default=dict)

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

    def get_user_ids(self):
        list_id = []
        for member in self.members.all():
            list_id.append(member.user_id)
        return list_id

    def get_member_ids(self):
        list_ids = []
        for member in self.members.all():
            list_ids.append(member.id)
        return list_ids

    def is_group(self):
        return self.get_member_ids().__len__() > 2

    @classmethod
    @sync_to_async
    def add_member_or_create(cls, thread_name, current_user, user_ids, is_encrypt=False):
        thread = cls.objects.filter(Q(leader_id__in=[current_user.id], name=thread_name))
        # add member only
        if thread.count() == 1 and not is_encrypt:
            thread = thread.first()
            member_list = thread.get_member_ids()
            for user_id in user_ids:
                if member_list.__contains__(user_id):
                    raise Exception(_('Invalid user list'))
                user = MemberInfo.verify_user_id(user_id)
                if user:
                    thread.members.add(user=user)
                    user.thread = thread.id + '|' + user.thread
                    user.save()
                else:
                    raise Exception(_('Invalid user.'))
            return True

        # create new thread
        elif thread.count() == 0:
            thread = cls.objects.create(name=thread_name, leader_id=current_user.id, is_encrypted=is_encrypt)
            thread.members.add(user=current_user)
            for user_id in user_ids:
                user = MemberInfo.verify_user_id(user_id)
                if user:
                    thread.members.add(user=user)
                    user.thread = thread.id + '|' + user.thread
                    user.save()
                else:
                    raise Exception(_('Invalid user'))
            thread.save()
            return True
        # raise exception if user not leader
        raise Exception(_('Invalid input.'))

    @classmethod
    @sync_to_async
    def member_count(cls, thread_name, current_user):
        thread = cls.objects.filter(Q(name=thread_name, members__id__contains=[current_user.id]))
        if thread.exists():
            return thread.first().members.count()
        raise Exception(_('Invalid input.'))

    @classmethod
    @sync_to_async
    def remove_or_leave(cls, thread_name, user_ids, current_user):
        thread = cls.objects.filter(Q(members__id__contains=[current_user.id], name=thread_name))
        if thread.exists():
            thread = thread.first()
            for user_id in user_ids:
                user = MemberInfo.verify_user_id(user_id)
                member = thread.members.filter(user=user).first()
                if member and (member.user_id == thread.leader_id or member.user_id == current_user.id):
                    member.delete()

                    thread_list = user.thread.split('|')
                    thread_list.remove(thread.id)
                    user.thread = '|'.join(thread_list)
                    user.save()
                else:
                    raise Exception(_('Invalid member list'))
        else:
            raise Exception(_('Invalid input'))
        return True

    @classmethod
    @sync_to_async
    def promotion(cls, thread_name, user_id, current_user):
        thread = cls.objects.filter(Q(name=thread_name, members__id__contains=[current_user.id]))
        if thread.exists():
            thread = thread.first()
            if thread.leader_id != user_id and thread.get_member_ids().__contains__(user_id):
                thread.leader_id = user_id
                thread.save()
            else:
                raise Exception(_('Invalid user id'))
        else:
            raise Exception(_('Invalid input.'))
        return True


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
