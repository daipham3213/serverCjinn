from django.contrib.auth.models import Permission
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from jsonfield import JSONField

from uuid import uuid4

from apps.auths.managers import GroupManager
from apps.auths.models import AuthUser
from apps.base.utils import phone_numbers_validator

TYPE_CHOICES = (
    ('web', _('Website')),
    ('mobile', _('Mobile')),
)


class RoleGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(_('name'), max_length=150)
    ref_id = models.UUIDField(null=True, default=None, verbose_name=_('reference ID'))
    ref_type = models.CharField(choices=settings.ROLE_GROUP_REF_TYPE, max_length=100, null=True, default=None)
    is_hidden = models.BooleanField(default=False)
    extras = JSONField(blank=True, null=True, default={})
    is_default = models.BooleanField(default=False)
    code_system = models.CharField(max_length=100, null=True, default=None)

    permissions = models.ManyToManyField(
        Permission,
        symmetrical=False,
        through='GroupPermission',
        verbose_name=_('permissions'),
        blank=True,
    )
    user_created = models.UUIDField(verbose_name=_('user created'), blank=False, null=True, editable=False)
    date_created = models.DateTimeField(verbose_name='date created', default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name='date modified', auto_now=True)

    objects = GroupManager()

    class Meta:
        verbose_name = _('role group')
        verbose_name_plural = _('role groups')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = (
            ('view_all_account_rolegroup', _('Can view all role group')),
            ('view_account_rolegroup', _('Can view role group')),
            ('add_account_rolegroup', _('Can add role group')),
            ('change_all_account_rolegroup', _('Can change all role group')),
            ('change_account_rolegroup', _('Can change role group')),
            ('delete_all_account_rolegroup', _('Can delete all role group')),
            ('delete_account_rolegroup', _('Can delete role group'))
        )

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name

    def save(self, *args, **kwargs):
        super(RoleGroup, self).save(*args, **kwargs)


class User(AuthUser):
    REQUIRED_FIELDS = ['phone', 'email']

    groups = models.ManyToManyField(
        RoleGroup,
        through='UserRoleGroup',
        symmetrical=False,
        verbose_name=_('user application groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='user_groups',
        related_query_name='user'
    )

    permissions = models.ManyToManyField(
        Permission,
        through='UserPermission',
        symmetrical=False,
        verbose_name=_('user application permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='user_permissions',
        related_query_name='user'
    )
    language = models.CharField(verbose_name=_("language"), max_length=10, choices=settings.LANGUAGE_CHOICE, blank=True,
                                null=True)
    is_delete = models.BooleanField(verbose_name=_('delete'), default=False)
    identity_key = models.TextField(verbose_name=_('identity key'), null=True, blank=True)
    discoverable_by_phone_number = models.BooleanField(verbose_name=_('discoverable by phone number'), default=True)

    def save(self, *args, **kwargs):
        if not getattr(self, 'username', None):
            self.username = self.phone if settings.LOGIN_VIA_PHONE else self.email
        if getattr(self, 'is_email', None) is False:
            if VerifyContact.objects.filter(email=self.email).exists():
                self.is_email = True
        if getattr(self, 'is_phone', None) is False:
            if VerifyContact.objects.filter(phone=self.phone).exists():
                self.is_phone = True
        super(User, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = (
            ('view_all_account_user', _('Can view all user')),
            ('view_account_user', _('Can view user')),
            ('add_account_user', _('Can add user')),
            ('change_all_account_user', _('Can change all user')),
            ('change_account_user', _('Can change user')),
            ('delete_all_account_user', _('Can delete all user')),
            ('delete_account_user', _('Can delete user'))
        )

# Login social
# class UserSocial(models.Model):
#     id = models.UUIDField(default=uuid4, primary_key=True, editable=False)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     provider = models.CharField(max_length=100)
#     uid = models.CharField(max_length=255)
#     extra_data = JSONField(default={})
#     secret_key = models.CharField(max_length=64)
#     date_created = models.DateTimeField(verbose_name='date created', default=timezone.now, editable=False)
#     date_modified = models.DateTimeField(verbose_name='date modified', auto_now=True, editable=False)
#
#     class Meta:
#         verbose_name = _('Provider User')
#         verbose_name_plural = _('Provider User')
#         unique_together = ('provider', 'uid')
#         ordering = ('-date_created',)
#         default_permissions = ()
#         permissions = ()
#
#     def save(self, *args, **kwargs):
#         if not self.secret_key:
#             self.secret_key = self.generate_secret_key(self.provider, self.uid, self.date_created)
#         super(UserSocial, self).save(*args, **kwargs)
#
#     @classmethod
#     def generate_secret_key(cls, provider, uid, user_id, date_created):
#         if provider and uid and user_id:
#             return hashlib.sha256('{}|{}|{}|{}'.format(str(provider), str(uid), str(user_id), str(date_created)[-3]).encode()).hexdigest()
#         raise ValueError("Provide, uid, user_id must be required when generate secret key social media network.")
#
#     @classmethod
#     def check_secret_key(cls, instance, secret_key):
#         return cls.generate_secret_key(instance.provider, instance.uid, instance.user_id, instance.date_created) == secret_key


class UserRoleGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    group = models.ForeignKey(RoleGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    extras = JSONField(blank=True, null=True, default={})

    class Meta:
        default_permissions = ()
        permissions = ()


class Staff(User):
    class Meta:
        proxy = True
        verbose_name = _('staff account')
        verbose_name_plural = _('staff accounts')
        default_permissions = ()
        permissions = ()


class VerifyContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(verbose_name=_('email address'), editable=False, null=True, blank=True)
    phone = models.CharField(verbose_name=_('phone number'), editable=False, null=True, blank=True, max_length=20,
                             validators=[phone_numbers_validator])

    is_valid = models.BooleanField(verbose_name=_('Valid email or phone after login'), default=True)
    counter = models.IntegerField(verbose_name=_('Counter user'), default=0)
    users = models.ManyToManyField(User, through='VerifyUser', symmetrical=False, blank=True,
                                   related_name='user_verify', related_query_name='users')
    date_created = models.DateTimeField(default=timezone.now)
    extras = JSONField(blank=True, null=True, default={})

    class Meta:
        verbose_name = _('Verify Contact Account')
        verbose_name_plural = _('Verify Contact Account')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = ()

    def __str__(self):
        return '{} - {}'.format(self.email if self.email else '', self.phone if self.phone else '')


class VerifyUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    verify = models.ForeignKey(VerifyContact, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)
    extras = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _('M2M Verify contact to User')
        verbose_name_plural = _('M2M Verify contact to User')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = ()

    def __str__(self):
        return '{}: {} {}'.format(self.user_id, self.user.first_name, self.user.last_name)

    def __unicode__(self):
        return u'{}: {} {}'.format(self.user_id, self.user.first_name, self.user.last_name)


class BackUpRoleSystem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    role_id = models.UUIDField(verbose_name=_('Role Group ID'), null=True, editable=False)
    ref_id = models.UUIDField(null=True, default=None, verbose_name=_('reference ID'))
    ref_type = models.CharField(choices=settings.ROLE_GROUP_REF_TYPE, max_length=100, null=True, default=None)
    is_hidden = models.BooleanField(default=False)
    extras = JSONField(blank=True, null=True, default={})
    is_default = models.BooleanField(default=False)
    code_system = models.CharField(max_length=100, null=True, default=None)
    permissions = JSONField(blank=True, null=True)
    user_list = JSONField(blank=True, null=True)
    date_created = models.DateTimeField(verbose_name='date created', default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name='date modified', auto_now=True)

    class Meta:
        verbose_name = _('Backup Role System Deleted')
        verbose_name_plural = _('Backup Role System Deleted')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = ()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.role_id:
            role = RoleGroup.objects.filter(id=self.role_id).first()
            if role:
                self.ref_id = role.ref_id
                self.ref_type = role.ref_type
                self.is_hidden = role.is_hidden
                self.extras = role.extras
                self.is_default = role.is_default
                self.code_system = role.code_system
                self.user_list = list(
                    UserRoleGroup.objects.filter(group_id=self.role_id).values_list('user_id', flat=True))
                self.permissions = list(role.permissions.all().values_list('codename', flat=True))
        super(BackUpRoleSystem, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                           update_fields=update_fields)
