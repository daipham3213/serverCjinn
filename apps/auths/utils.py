from django.conf import settings
from django.core.mail import send_mail
from django.db import connection
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from phonenumbers import carrier

import phonenumbers

from apps.base import status
from apps.base.models import Token

STATUS = {
    'status': None,
    'message': None,
}


def too_many_requests():
    STATUS['status'] = status.HTTP_429_TOO_MANY_REQUESTS
    STATUS['message'] = _('Reached max limit for the day.')
    return STATUS, STATUS['status']


def unauthorized():
    STATUS['status'] = status.HTTP_401_UNAUTHORIZED
    STATUS['message'] = _('User not logged in.')
    return STATUS, STATUS['status']


def failure(message=None):
    STATUS['status'] = status.HTTP_401_UNAUTHORIZED
    STATUS['message'] = _('Failed') if not message else message
    return STATUS, STATUS['status']


def success(message=None):
    STATUS['status'] = status.HTTP_200_OK
    STATUS['message'] = '' if not message else message
    return STATUS, STATUS['status']


def mobile_validate(phone):
    phone = phonenumbers.parse(phone, getattr(settings, 'PHONENUMBER_DEFAULT_REGION', 'VN'))
    return carrier.number_type(phone)


def mobile_phone_format(phone):
    x = phonenumbers.parse(phone, getattr(settings, 'PHONENUMBER_DEFAULT_REGION', 'VN'))
    return phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.E164)


def user_details(request, user, last_login):
    try:
        is_superuser = request.user.is_superuser
        is_staff = request.user.is_staff
    except Exception as e:
        is_superuser = False
        is_staff = False

    token, created = Token.objects.get_or_create(user=user)
    # id_n
    ctx = {
        'id': user.id,
        'id_n': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': str(user.phone),
        'language': user.language,
        'others': {
            'is_email': user.is_email,
            'is_phone': user.is_phone,
            'is_staff': is_staff,
            'is_superuser': is_superuser,
        },
        'avatar': user.avatar,
        'last_login': last_login,
        'is_first_login': True if last_login is None else False,
        'token': token.key
    }
    return ctx


def send_otp(otp, account):
    try:
        send_mail(
            subject=getattr(settings, 'EMAIL_OTP_SUBJECT'),
            message=render_to_string(
                'account_auth/email_otp.txt',
                {'otp': otp, 'project_name': settings.PROJECT_NAME, 'expire': getattr(settings, 'LOGIN_OTP_EXPIRE', 15)}
            ),
            from_email=settings.EMAIL_HOST_USER, recipient_list=[account])
    except Exception as e:
        print(e)
    connection.close()
    return True


def send_otp_create_user(account, data, is_thread=False):
    try:
        html_message = render_to_string(
            'account_auth/add_user/email_otp_add_user.html',
            {
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'username': data.get('username', ''),
                'password': data.get('password', ''),
                'org_name': data.get('name', ''),
                'link_client': data.get('link_client', '')
            }
        )
        send_mail(
            subject='[{}][{}] {} {} {} to {} company'.format(
                getattr(settings, 'SYSTEM_CMIS_ONLINE', ''),
                data.get('name', ''),
                getattr(settings, 'EMAIL_ADD_USER_SUBJECT', 'Welcome'),
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('name', '')
            ),
            message="",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[account],
            html_message=html_message
        )
    except Exception as e:
        print(e)
    connection.close()


def send_request_valid_email(account, data, is_thread=False):
    try:
        html_message = render_to_string(
            'account_auth/send_request_valid_email.html',
            {
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'username': data.get('username', ''),
                'otp': data.get('otp', ''),
                'org_name': data.get('org_name', ''),
                'link_client': data.get('link_client', ''),
                'expire_hour': getattr(settings, 'EXPIRE_VALID_USER', 24)
            }
        )
        send_mail(
            subject='[{}] {}'.format(data.get('org_name', ''), 'Valid email in system'),
            message="",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[account],
            html_message=html_message
        )
    except Exception as e:
        print(e)
    connection.close() if is_thread else None
    return True
