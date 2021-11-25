import logging
import uuid as uuid
from re import sub
from threading import local
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils import translation, timezone
from django.utils.deprecation import MiddlewareMixin

from apps.account.models import User
from apps.base.mixins import Output
from apps.base.models import Token
from apps.messenger.models import DeviceInfo

logger = logging.getLogger(__name__)

_thread_locals = local()


def get_user_extra():
    return getattr(_thread_locals, 'user_extra', None)


class CjinnMiddleware(MiddlewareMixin, Output):
    def process_request(self, request):
        is_dropdown = True if request.META.get('HTTP_VIEWTOKEN', False) == settings.KEY_VIEW_TOKEN else False
        device_token = request.META.get('HTTP_DEVICE_TOKEN', None)
        header_token = request.META.get('HTTP_AUTHORIZATION', None)
        if device_token is not None:
            try:
                device_token = sub('Bearer ', '', request.META.get('HTTP_DEVICE_TOKEN', None))
                device = DeviceInfo.objects.get(token=device_token)
                # mark stale devices
                device.last_seen = timezone.now()
                device.is_stale = False
                device.save()
                for other_device in DeviceInfo.objects.exclude(token=device_token):
                    other_device.is_stale = True
                    other_device.save()

                request.device = device
                request.user = device.user
            except DeviceInfo.DoesNotExist:
                pass
        elif header_token is not None:
            try:
                token = sub('Bearer ', '', request.META.get('HTTP_AUTHORIZATION', None))
                token_obj = Token.objects.get(key=token)
                request.user = token_obj.user
            except Token.DoesNotExist:
                request.user = AnonymousUser()
                request.device = None
                header_language = request.META.get('HTTP_LANGUAGE', None)
                if header_language is not None:
                    if header_language in dict(settings.LANGUAGE_CHOICE):
                        request.session['LANGUAGE'] = header_language
                        translation.activate(header_language)
        else:
            request.user = AnonymousUser()
            request.device = None
            header_language = request.META.get('HTTP_LANGUAGE', None)
            if header_language is not None:
                if header_language in dict(settings.LANGUAGE_CHOICE):
                    request.session['LANGUAGE'] = header_language
                    translation.activate(header_language)
        user = getattr(request, 'user', None)
        device = getattr(request, 'device', None)
        if hasattr(user, 'is_authenticated') and user.is_authenticated and not user.is_staff:
            try:
                _thread_locals.user_extra = request.user_extra = {
                    'is_dropdown': is_dropdown,
                    'user': user,
                    'token': header_token,
                    'is_admin': user.is_superuser | user.is_staff,
                    'device': device
                }

                # language
                header_language = request.META.get('LANGUAGE', None) if \
                    request.META.get('LANGUAGE', None) else request.META.get('HTTP_LANGUAGE', None)
                if header_language is not None:
                    if header_language in dict(settings.LANGUAGE_CHOICE):
                        request.session['LANGUAGE'] = header_language
                        translation.activate(header_language)
                else:
                    if request.session.get('lang', None):
                        translation.activate(request.session.get('lang'))
                    elif user.language:
                        translation.activate(user.language)
                        request.session['LANGUAGE'] = user.language
                    else:
                        pass
            except Exception as e:
                print(e)


ONLINE_THRESHOLD = getattr(settings, 'ONLINE_THRESHOLD', 60 * 15)
ONLINE_MAX = getattr(settings, 'ONLINE_MAX', 50)


def get_online_now(self):
    return User.objects.filter(id__in=self.online_now_ids or [])


class OnlineNowMiddleware(MiddlewareMixin):
    """
    Maintains a list of users who have interacted with the website recently.
    Their user IDs are available as ``online_now_ids`` on the request object,
    and their corresponding users are available (lazily) as the
    ``online_now`` property on the request object.
    """

    def process_request(self, request):
        # First get the index
        ids = cache.get('online-now', [])

        # Perform the multiget on the individual online uid keys
        online_keys = ['online-%s' % (u,) for u in ids]
        fresh = cache.get_many(online_keys).keys()
        online_now_ids = [uuid.UUID(k.replace('online-', '')) for k in fresh]

        # If the user is authenticated, add their id to the list
        if request.user.is_authenticated:
            uid = request.user.id
            # If their uid is already in the list, we want to bump it
            # to the top, so we remove the earlier entry.
            if uid in online_now_ids:
                online_now_ids.remove(uid)
            online_now_ids.append(uid)
            if len(online_now_ids) > ONLINE_MAX:
                del online_now_ids[0]

        # Attach our modifications to the request object
        request.__class__.online_now_ids = online_now_ids
        request.__class__.online_now = property(get_online_now)

        # Set the new cache
        cache.set('online-%s' % (request.user.pk,), True, ONLINE_THRESHOLD)
        cache.set('online-now', online_now_ids, ONLINE_THRESHOLD)


@database_sync_to_async
def get_user_by_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        params = parse_qs(scope["query_string"].decode())
        scope['user'] = await get_user_by_token(params.get('token', None))

        return await super().__call__(scope, receive, send)
