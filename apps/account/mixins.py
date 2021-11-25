import logging

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.account import exceptions
from apps.account.constants import Messages
from apps.auths.models import Token
from apps.auths.utils import user_details
from apps.base.middleware import get_user_extra
from apps.base.mixins import Output
from apps.base.utils import format_message, check_uuid, json_parser
from apps.log.func import authorization_log, activity_log

UserModel = get_user_model()
logger = logging.getLogger(__name__)

utc = pytz.UTC


class AuthRegisterMixin(Output):
    @classmethod
    def verifier(cls, username, email):
        # valid user name
        try:
            valid_username = UnicodeUsernameValidator()
            valid_username(username)
            user = UserModel.objects.filter(username=username)
            if user:
                raise exceptions.UsernameAlreadyInUse
        except ValidationError:
            raise exceptions.InvalidUsername

        # valid password
        try:
            valid_email = EmailValidator()
            valid_email(email)
            user = UserModel.objects.filter(email=email)
            if user:
                raise exceptions.EmailAlreadyInUse
        except ValidationError:
            raise exceptions.InvalidEmail
        return username, email

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        logger.info(format_message(cls, info.context.method, 'begin', '', '', info.context.body))
        try:
            username = kwargs.get('username')
            email = kwargs.get('email')
            others = {
                'first_name': kwargs.get('first_name'),
                'last_name': kwargs.get('first_name'),
            }

            username, email = cls.verifier(username, email)

            token = Token.create_otp(account=email, username=username, others=others, is_register=True)
            if token:
                cls.verifier(username, email)
                email_token = token
                result = {
                    'verify_id': email_token.id,
                    'created_at': email_token.date_created.replace(tzinfo=utc),
                    'expire_in': settings.LOGIN_OTP_EXPIRE
                }
                logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 200))
                return cls(success=True, result={**result})
            else:
                return cls(success=False, errors={Messages.ATTEMPTS_EXCEEDED})

        except exceptions.EmailAlreadyInUse:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
            return cls(success=False, errors={'email': Messages.EMAIL_IN_USE}, )
        except exceptions.UsernameAlreadyInUse:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
            return cls(success=False, errors={'username': Messages.USERNAME_IN_USE}, )
        except exceptions.InvalidEmail:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
            return cls(success=False, errors={'email': Messages.INVALID_EMAIL}, )
        except exceptions.InvalidUsername:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
            return cls(success=False, errors={'email': Messages.INVALID_USERNAME}, )


class AuthOTPValidMixin(Output):
    @classmethod
    def verifier(cls, pk, otp=''):
        if (pk or otp) is not None:
            if pk is None:
                if 0 < len(otp) < 20:
                    return pk, otp
            elif check_uuid(pk):
                return pk, otp
        raise ValueError(_('Invalid token'))

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        logger.info(format_message(cls, info.context.method, 'begin', '', '', info.context.body))
        try:
            pk = kwargs.get('pk', None)
            otp = kwargs.get('otp', None)
            if isinstance(otp, str):
                otp = otp.replace(" ", "")
            cls.verifier(pk, otp)
            user = authenticate(info.context, pk=pk, otp=otp)
            if user and user.is_active:
                last_login = user.last_login
                login(info.context, user)
                result = user_details(info.context, user, last_login)
                authorization_log(user=user.id, remarks=_('The user validation otp success.'), data={})
                logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, result))
                return cls(success=True, result={**result})
            else:
                logger.info(format_message(cls, info.context.method, 'fail', '', '', None, _('OTP does not exists')))
                return cls(success=False, errors=Messages.INVALID_TOKEN)
        except ValueError:
            logger.info(format_message(cls, info.context.method, 'fail', '', '', None, _('OTP does not exists')))
            return cls(success=False, errors=Messages.INVALID_TOKEN)


class AuthOTPResendMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        pk = kwargs.get('pk', None)
        if pk:
            otp = Token.objects.filter(pk=pk, is_active=False).first()
            if otp:
                new_token = Token.create_otp(
                    account=otp.phone if getattr(settings, 'LOGIN_VIA_PHONE', False) else otp.email,
                    username=otp.username,
                    others=otp.others, is_register=otp.is_register,
                    data=otp.data, is_valid=otp.is_valid, email_change=otp.email_change, phone_change=otp.phone_change
                )
                otp.is_delete = True
                otp.save()
                return cls(success=True, result={
                    'verify_id': json_parser(new_token.id),
                    'created_at': json_parser(new_token.date_created),
                    'expire_in': settings.LOGIN_OTP_EXPIRE
                })
        return cls(success=False, errors={Messages.INVALID_TOKEN})


class AuthLoginMixin(Output):

    @classmethod
    def account_validator(cls, username=None):
        is_email = False
        if username is None:
            raise exceptions.InvalidCredentials
        try:
            validator = EmailValidator()
            validator(username)
            is_email = True
            return username, is_email
        except ValidationError:
            try:
                validator = UnicodeUsernameValidator()
                validator(username)
                return username, is_email
            except ValidationError:
                raise exceptions.InvalidUsername

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        username = kwargs.get('username', None)
        password = kwargs.get('password', None)

        try:
            account, is_email = cls.account_validator(username)
            user = authenticate(email=account, password=password) if is_email else authenticate(username=account,
                                                                                                password=password)
            if user and user.is_active:
                last_login = user.last_login
                login(info.context, user)
                result = user_details(info.context, user, last_login)
                authorization_log(user=user.id, remarks=_('user logged in.'), data={})
                return cls(success=True, result={**result})
            return cls(success=False, errors={'username': Messages.INVALID_CREDENTIALS})
        except exceptions.InvalidEmail as e:
            logger.error(format_message(cls, info.context.method, 'error', '', '', info.context.data, e))
            return cls(sucess=False, errors={'email': Messages.INVALID_EMAIL})
        except exceptions.InvalidUsername as e:
            logger.error(format_message(cls, info.context.method, 'error', '', '', info.context.data, e))
            return cls(sucess=False, errors={'email': Messages.INVALID_USERNAME})


class ChangePasswordMixin(Output):

    @classmethod
    def validator(cls, password_old, password_new):
        if (password_old and password_new) is None:
            raise ValidationError(_('New password and old password must be filled.'))
        if password_new == password_old:
            raise exceptions.PasswordAlreadySetError

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        request = info.context
        try:
            user_org = get_user_extra()
            if user_org:
                user = user_org['user']
                logger.info(
                    format_message(cls, request.method, 'begin', request.user.username, request.user.id, request.body,
                                   None, user.id))

                pw_old = kwargs.get('password_old')
                pw_new = kwargs.get('password_new')
                cls.validator(pw_old, pw_new)

                if not user.check_password(pw_old):
                    logger.info(
                        format_message(cls, request.method, 'fail', request.user.username, request.user.id, None,
                                       _('Wrong password')))
                    raise ValidationError(_('Wrong password'))
                user.set_password(pw_new)
                user.save()
                if hasattr(request, 'user_extra') and hasattr(request, 'user'):
                    user = request.user
                    activity_log(
                        user=user.id, remarks=_('The user changed password.'), doc_id=None, code_document='System',
                        data={}, is_system=True, date_created=timezone.now()
                    )
                logger.info(format_message(cls, request.method, 'success', request.user.username, request.user.id))
                return cls(success=True, result={'result': _('Password updated successfully')})
            return cls(success=False, errors={'message': Messages.INVALID_CREDENTIALS})
        except Exception as e:
            logger.error(
                format_message(cls, request.method, 'error', request.user.username, request.user.id, request.body, e))
            return cls(success=False, errors={'message': e})


class ResetPasswordMixin(Output):
    @classmethod
    def verifier(cls, username):
        try:
            validator = UnicodeUsernameValidator()
            validator(username)
            user = UserModel.objects.get(username=username)
            if user:
                return user.username, user.email
        except ValidationError:
            raise ValidationError(_('Invalid username'))

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        request = info.context
        logger.info(format_message(cls, request.method, 'begin', None, None, request.body, None, None))
        try:
            username = kwargs.get('username')
            username, email = cls.verifier(username)

            token = Token.create_otp(account=email, username=username)
            if token:
                logger.info(format_message(cls, request.method, 'success', None, None, request.data, True))
                activity_log(
                    user=token.username, remarks=_('The user reset password.'), doc_id=None, code_document='System',
                    data={}, is_system=True, date_created=timezone.now()
                )
                return cls(success=True, result={
                    'verify_id': token.id,
                    'created_at': token.date_created,
                    'expire_in': settings.LOGIN_OTP_EXPIRE
                })
            else:
                logger.info(format_message(cls, request.method, 'success', None, None, request.data, True))
                return cls(success=False, errors={
                    'message': _('You can not have more than {} attempts per day, please try again tomorrow').format(
                        getattr(settings, 'LOGIN_ATTEMPTS', 10))
                })
        except Exception as e:
            logger.error(
                format_message(cls, request.method, 'error', request.user.username, request.user.id, request.body, e))
            return cls(success=False, errors={'message': e})
