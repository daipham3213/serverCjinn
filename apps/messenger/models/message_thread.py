from uuid import uuid4

from cloudinary.models import CloudinaryField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.messenger.models import UserInfo

UserModel = get_user_model()


class MemberInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_info = models.ForeignKey(UserInfo, verbose_name=_('member info'), on_delete=models.CASCADE)
    thread = models.ForeignKey('Thread', verbose_name=_('thread info'), on_delete=models.CASCADE)

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
    members = models.ManyToManyField(
        UserInfo,
        through=MemberInfo,
        verbose_name=_('Members of the thread'),
        symmetrical=False,
        blank=True,
    )
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
            list_id.append(member.user_info.user_id)
        return list_id

    def get_member_ids(self):
        list_ids = []
        for member in self.members.all():
            list_ids.append(member.id)
        return list_ids

    def is_group(self):
        return self.members.count() > 2

    @classmethod
    def get_thread_by_list_user(cls, user_ids, is_encrypted=False):
        user_infos = UserInfo.objects.filter(user_id__in=user_ids)
        # q = Q(is_encrypted=is_encrypted)
        # for user_info in target_users:
        #     q &= Q(memberinfo__user_info=user_info)
        result = Thread.objects.annotate(counter=Count('memberinfo')).filter(counter=len(user_infos))
        for member in user_infos:
            result = result.filter(memberinfo__user_info=member)
        return result

    @classmethod
    def get_or_create_thread(cls, thread_name, current_user, user_ids, is_encrypted=False):
        user_ids.append(current_user.id)
        thread = cls.get_thread_by_list_user(user_ids, is_encrypted)
        #  return the thread if it exists
        if thread.count() == 1:
            thread = thread.first()
            return thread

        # create new thread
        elif thread.count() == 0 and ((user_ids.__len__() < 3 and is_encrypted) or not is_encrypted):
            thread = Thread.objects.create(
                name=thread_name, leader_id=current_user.id, is_encrypted=is_encrypted)
            for user_id in user_ids:
                user_info = UserInfo.objects.get(user_id=user_id)
                if user_info:
                    MemberInfo.objects.create(
                        user_info=user_info, thread=thread)
                else:
                    raise Exception(_('Invalid user'))
            # current_user_info = UserInfo.objects.get(user_id=current_user.id)
            # MemberInfo.objects.create(user_info=current_user_info, thread=thread)
            thread.save()
            return thread
        # raise exception if user not leader
        raise Exception(_('Invalid input.'))

    @classmethod
    def member_count(cls, thread_id, current_user):
        thread = Thread.objects.filter(
            Q(id=thread_id, memberinfo__user_info__user=current_user))
        if thread.exists():
            return thread.first().members.count()
        raise Exception(_('Invalid input.'))

    @classmethod
    def remove_or_leave(cls, thread_id, user_ids, current_user):
        thread = Thread.objects.get(id=thread_id)
        if thread.exists():
            user_infos = UserInfo.objects.filter(user_id__in=user_ids)
            current_user_info = UserInfo.objects.get(user=current_user)
            for member in thread.members.filter(user__in=user_infos):
                if (thread.leader_id == current_user.id) or (member.user == current_user_info):
                    member.delete()
                else:
                    raise Exception(_('Invalid member list'))
            if thread.members.count() == 0:
                thread.delete()
            else:
                thread.save()
        else:
            raise Exception(_('Invalid input'))
        return True

    @classmethod
    def promotion(cls, thread_id, user_id, current_user):
        thread = cls.objects.filter(
            Q(name=thread_id, memberinfo__user_info__user=current_user, leader_id=current_user.id))
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

    extras = models.JSONField(blank=True, null=True, default=dict)
    user_created = models.UUIDField(verbose_name=_('user created'), null=True, blank=True)
    date_created = models.DateTimeField(verbose_name=_('created date'), default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name=_('modified date'), default=timezone.now)
    is_deleted = models.BooleanField(default=False)
    destination = models.UUIDField()

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


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    image = CloudinaryField('image', null=True, blank=True)
    video = CloudinaryField('video', null=True, blank=True)

    user_created = models.UUIDField(verbose_name=_('create by'), blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now, editable=False)
    thread_id = models.UUIDField()

    class Meta:
        verbose_name = _('attachment')
        verbose_name_plural = _('attachments')
        default_permissions = ()
