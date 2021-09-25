from threading import Thread

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, Permission
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

from .managers import AccountManager
from datetime import datetime, date, time
from uuid import uuid4

import os
import hashlib

from .utils import send_otp, send_request_valid_email
from ..base.utils import phone_numbers_validator


class AuthUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        verbose_name=_('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _('A user with that username already exists.'),
        },
    )
    first_name = models.CharField(verbose_name=_('first name'), max_length=80, blank=True, null=True)
    last_name = models.CharField(verbose_name=_('last name'), max_length=150, blank=True, null=True)
    email = models.EmailField(verbose_name=_('email address'), null=True, blank=True)
    phone = models.CharField(verbose_name=_('phone number'), null=True, blank=True, max_length=20,
                             validators=[phone_numbers_validator])
    dob = models.DateField(verbose_name=_('birthday'), blank=True, null=True)
    gender = models.CharField(verbose_name=_('gender'), choices=settings.GENDER_CHOICE, max_length=6, blank=True,
                              null=True)
    language = models.CharField(verbose_name=_('language'), choices=settings.LANGUAGE_CHOICE, max_length=4,
                                default='vi', null=True)
    avatar = models.TextField(blank=True, null=True, verbose_name=_('avatar path'))
    is_phone = models.BooleanField(verbose_name=_('phone is valid'), default=False)
    is_email = models.BooleanField(verbose_name=_('email is valid'), default=False)
    is_active = models.BooleanField(verbose_name=_('active'), default=True)
    is_staff = models.BooleanField(verbose_name=_('staff status'), default=False)
    is_superuser = models.BooleanField(default=False, verbose_name=_('superuser'))
    user_created = models.UUIDField(verbose_name=_('user created'), null=True, editable=False)
    date_created = models.DateTimeField(verbose_name=_('date created'), default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name=_('date modified'), auto_now=True, editable=False)
    date_joined = models.DateTimeField(verbose_name=_('date joined'), default=timezone.now, editable=False)
    extras = JSONField(blank=True, null=True, default={})

    objects = AccountManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return u'{} {}'.format(self.last_name, self.first_name)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True
        default_permissions = ()
        permissions = ()


class Token(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    username = models.CharField(max_length=100, editable=False, null=True, blank=True)
    username_change = models.CharField(verbose_name=_('username change'), max_length=100, editable=False, null=True,
                                       blank=True)
    email = models.EmailField(verbose_name=_('email address'), editable=False, null=True, blank=True)
    email_change = models.EmailField(verbose_name=_('email change'), editable=False, null=True, blank=True)
    phone = models.CharField(verbose_name=_('phone number'), editable=False, null=True, blank=True, max_length=20,
                             validators=[phone_numbers_validator])
    phone_change = models.CharField(verbose_name=_('phone number change'), editable=False, null=True, blank=True,
                                    max_length=20,
                                    validators=[phone_numbers_validator])
    otp = models.CharField(max_length=40, editable=False)
    date_created = models.DateTimeField(verbose_name=_('date created'), default=timezone.now, editable=False)
    attempts = models.PositiveSmallIntegerField(verbose_name=_('attempts'), default=0)

    others = JSONField(verbose_name=_('others'), blank=True, default={})
    data = JSONField(default={})
    is_delete = models.BooleanField(default=False)
    is_register = models.BooleanField(verbose_name=_('org register'), default=False)
    is_active = models.BooleanField(verbose_name=_('active'), default=False)
    is_valid = models.BooleanField(verbose_name=_('Valid email or phone after login'), default=False)
    extras = JSONField(blank=True, null=True, default={})

    class Meta:
        app_label = 'account'
        verbose_name = _('OTP Token')
        verbose_name_plural = _('OTP Tokens')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = ()

    def __str__(self):
        return '{} - {}'.format(self.phone, self.otp)

    @classmethod
    def create_otp(cls, account, username, others=None, is_register=False, is_valid=False, data={}, email_change=None,
                   phone_change=None):
        is_phone = getattr(settings, 'LOGIN_VIA_PHONE', False)
        today_min = datetime.combine(date.today(), time.min)
        today_max = datetime.combine(date.today(), time.max)
        result = cls.objects.filter(username=username).filter(date_created__range=(today_min, today_max))
        if result.count() < getattr(settings, 'LOGIN_ATTEMPTS', 10):
            otp = cls.generate_otp(length=getattr(settings, 'LOGIN_OTP_LENGTH', 6))
            auth_token = Token(username=username, phone=account, otp=otp) if is_phone else Token(username=username,
                                                                                                 email=account, otp=otp)
            if is_register:
                auth_token.others = others
                auth_token.is_register = is_register

            auth_token.save()
            if settings.LOGIN_OTP_SEND:
                if is_valid:
                    try:
                        if email_change:
                            auth_token.email_change = email_change
                        if phone_change:
                            auth_token.phone_change = phone_change
                        auth_token.is_valid = True
                        auth_token.data = data
                        auth_token.save()
                        data = {
                            'first_name': data.get('first_name', ''),
                            'last_name': data.get('last_name', ''),
                            'username': data.get('username', ''),
                            'link_client': data.get('client_host', '') + '?verify_id=' + str(auth_token.id),
                            'otp': otp
                        }
                        _thread = Thread(target=send_request_valid_email, args=(account, data),
                                         kwargs={"is_thread": True}, daemon=True).start()
                    except Exception as e:
                        print(e)
                else:
                    try:
                        _thread = Thread(target=send_otp, args=(otp, account), kwargs={}, daemon=True).start()
                    except Exception as e:
                        print(e)
            return auth_token
        return False

    @classmethod
    def generate_otp(cls, length=6):
        algorithm = getattr(settings, 'LOGIN_OTP_HASH_ALGORITHM', 'sha256')
        m = getattr(hashlib, algorithm)()
        m.update(getattr(settings, 'SECRET_KEY', None).encode('utf-8'))
        m.update(os.urandom(16))
        otp = str(int(m.hexdigest(), 16))[-length:]
        return otp
