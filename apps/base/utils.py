from uuid import UUID
from re import sub
import datetime
import decimal
import json  # noqa
import uuid

from django.conf import settings
from django.core import signing
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import phonenumbers

from apps.account.exceptions import TokenScopeError


def check_uuid(text, version=4):
    try:
        UUID(str(text), version=4)
        return True
    except Exception as e:
        return False


def serializer_data(obj, keys=None):
    for key in dir(obj):
        if key not in dir(obj.__class__):
            if keys is not None and key in keys:
                return dict((key, getattr(obj, key)))
            else:
                return dict((key, getattr(obj, key)))


def phone_numbers_validator(value):
    result = phonenumbers.parse(value, getattr(settings, 'PHONENUMBER_DEFAULT_REGION', 'VN'))
    if not result:
        raise ValidationError(_('%(value)s is not a phone number'),
                              params={'value': value},
                              )


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time/timedelta,
    decimal types, generators and other basic python objects.
    """

    def default(self, obj):
        # For Date Time string spec, see ECMA 262
        # https://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(obj, Promise):
            return force_str(obj)
        elif isinstance(obj, datetime.datetime):
            representation = obj.isoformat()
            if representation.endswith('+00:00'):
                representation = representation[:-6] + 'Z'
            return representation
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            if timezone and timezone.is_aware(obj):
                raise ValueError("JSON can't represent timezone-aware times.")
            representation = obj.isoformat()
            return representation
        elif isinstance(obj, datetime.timedelta):
            return str(obj.total_seconds())
        elif isinstance(obj, decimal.Decimal):
            # Serializers will coerce decimals to strings by default.
            return float(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, QuerySet):
            return tuple(obj)
        elif isinstance(obj, bytes):
            # Best-effort for binary blobs. See #4187.
            return obj.decode()
        elif hasattr(obj, 'tolist'):
            # Numpy arrays and array scalars.
            return obj.tolist()
        elif hasattr(obj, '__getitem__'):
            cls = (list if isinstance(obj, (list, tuple)) else dict)
            try:
                return cls(obj)
            except Exception:
                pass
        elif hasattr(obj, '__iter__'):
            return tuple(item for item in obj)
        return super().default(obj)


def json_parser(obj):
    return json.dumps(obj, cls=JSONEncoder, default=str)


def get_token(user, action, **kwargs):
    username = user.get_username()
    if hasattr(username, "pk"):
        username = username.pk
    payload = {user.USERNAME_FIELD: username, "action": action}
    if kwargs:
        payload.update(**kwargs)
    token = signing.dumps(payload)
    return token


def get_token_payload(token, action, exp=None):
    payload = signing.loads(token, max_age=exp)
    _action = payload.pop("action")
    if _action != action:
        raise TokenScopeError
    return payload


def using_refresh_tokens():
    if (
            hasattr(settings, "GRAPHQL_JWT")
            and settings.GRAPHQL_JWT.get("JWT_LONG_RUNNING_REFRESH_TOKEN", False)
            and "graphql_jwt.refresh_token.apps.RefreshTokenConfig"
            in settings.INSTALLED_APPS
    ):
        return True
    return False


def revoke_user_refresh_token(user):
    if using_refresh_tokens():
        refresh_tokens = user.refresh_tokens.all()
        for refresh_token in refresh_tokens:
            try:
                refresh_token.revoke()
            except Exception:  # JSONWebTokenError
                pass


def flat_dict(dict_or_list):
    """
    if is dict, return list of dict keys,
    if is list, return the list
    """
    return list(dict_or_list.keys()) if isinstance(dict_or_list, dict) else dict_or_list


def normalize_fields(dict_or_list, extra_list):
    """
    helper merge settings defined fileds and
    other fields on mutations
    """
    if isinstance(dict_or_list, dict):
        for i in extra_list:
            dict_or_list[i] = "String"
        return dict_or_list
    else:
        return dict_or_list + extra_list


def format_message(api, method, status, username, user_id, body=None, message=None, data=None):
    try:
        result = {
            'api_name': api.__name__,
            'api_method': method,
            'api_status': status,
            'api_content': body,
            'user': '{}-{}'.format(username, user_id),
            'message': str(message),
            'data': str(data)
        }
        return json.dumps(result)
    except Exception as e:
        print(e)
