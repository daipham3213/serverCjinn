from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from django.db.models import F

import datetime
import pytz

from apps.account.models import VerifyContact, VerifyUser
from apps.auths.models import Token

utc = pytz.UTC


class AccountBackend(ModelBackend):
    def __init__(self, *args, **kwargs):
        self.user_model = get_user_model()

    @classmethod
    def sync_verify_account(cls, user_id, email=None, phone=None):
        kwargs = {}
        if email:
            kwargs.update({'email': email})
        if phone:
            kwargs.update({'phone': phone})

        if kwargs:
            verify_account = VerifyContact.objects.filter(**kwargs).first()
            if verify_account:
                verify_user = VerifyUser.objects.filter(verify=verify_account, user_id=user_id).first()
                if verify_user:
                    VerifyUser.objects.create(verify=verify_account, user_id=user_id)
                    verify_account.counter = F('counter') + 1
                    verify_account.save()
            else:
                verify_account = VerifyContact.objects.create(**kwargs)
                VerifyUser.objects.create(verify=verify_account, user_id=user_id)
                verify_account.counter = F('counter') + 1
                verify_account.save()
            return True
        return False

    @classmethod
    def get_username_data(cls, username):
        username_field = getattr(settings, 'USERNAME_FIELD', 'username')
        data = {username_field: username}
        return data

    @classmethod
    def get_phone_data(cls, phone):
        phone_field = getattr(settings, 'PHONE_FIELD', 'phone')
        data = {phone_field: phone}
        return data

    @classmethod
    def get_email_data(cls, email):
        email_field = getattr(settings, 'EMAIL_FIELD', 'email')
        data = {email_field: email}
        return data

    def create_user(self, token, **extra_fields):
        """
        Create and return the user based on the token.
        """
        username = token.username
        phone = token.phone
        email = token.email
        is_phone = False
        is_email = False

        via_phone = getattr(settings, 'LOGIN_VIA_PHONE', False)
        if via_phone:
            is_phone = True
        else:
            is_email = True

        kwargs = {
            'password': extra_fields.get('password', token.otp),
            'first_name': token.others.get('first_name', None),
            'last_name': token.others.get('last_name', None),
            'is_phone': is_phone,
            'is_email': is_email
        }
        kwargs.update(self.get_username_data(username=username))
        kwargs.update(self.get_phone_data(phone))
        kwargs.update(self.get_email_data(email))
        user = self.user_model.objects.create_user(**kwargs)
        if is_phone:
            self.sync_verify_account(user_id=user.id, phone=user.phone)
        elif is_email:
            self.sync_verify_account(user_id=user.id, email=user.email)
        return user

    def authenticate(self, request=None, pk=None, otp=None, change_pass=True, **extra_fields):
        # 1. Validating the Token with PK and OTP.
        # 2. Check if token and otp are same, within the given time range
        try:
            token = Token.objects.get(pk=pk, otp=otp, is_active=False, is_delete=False)
            if token.is_valid:
                time_difference = datetime.datetime.now() - datetime.timedelta(
                    hours=getattr(settings, 'EXPIRE_VALID_USER', 24))
            else:
                time_difference = datetime.datetime.now() - datetime.timedelta(
                    minutes=getattr(settings, 'LOGIN_OTP_EXPIRE', 15))
            if token.date_created < time_difference:
                return None
        except Token.DoesNotExist:
            return None

        # 3. Create new user if it doesn't exist
        user = self.user_model.objects.filter(**self.get_username_data(token.username)).first()
        try:
            with transaction.atomic():
                if not user:
                    user = self.create_user(
                        token=token,
                        **extra_fields
                    )
                elif otp:
                    if change_pass:
                        if not token.is_valid:
                            user.set_password(otp)
                            user.save()
                        if token.email_change:
                            user.email = token.email_change
                            user.is_email = True
                            user.save()
                        if token.phone_change:
                            user.phone = token.phone_change
                            user.is_phone = True
                            user.save()

                if not token.is_register:
                    # update validating email/phone status
                    if token.email:
                        user.is_email = True
                        self.sync_verify_account(user_id=user.id, email=user.email)
                    elif token.phone:
                        user.is_phone = True
                        self.sync_verify_account(user_id=user.id, phone=user.phone)
                    user.save()

                token.is_active = True
                token.attempts += 1
                token.save()

                return user
        except Exception as e:
            print(e)
            return e
