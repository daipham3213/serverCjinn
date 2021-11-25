import graphene
from channels_graphql_ws import Subscription
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.base.converter import AutoCamelCasedScalar
from apps.messenger.constants import FRIEND_ONLINE, INCOMING_MGS
from apps.messenger.func import cache_prefix, get_user_cache, add_or_update_user_cache
from apps.messenger.models import UserInfo, DeviceInfo


class FriendOnlineSubscription(Subscription):
    notification_queue_limit = settings.CLIENTS_LIMIT

    # payload
    event = AutoCamelCasedScalar()

    class Arguments:
        registration_id = graphene.UUID()

    @staticmethod
    def subscribe(root, info, *args, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            device = info.context.device
            if device is None:
                device = DeviceInfo.objects.filter(registration_id=kwargs.get('registration_id'),
                                                   user_id=user.id).first()
            if user.is_authenticated and device:
                del info
                add_or_update_user_cache(user_id=user.id, device_id=device.id, friend_online=True)
                prefix = cache_prefix(FRIEND_ONLINE, user.id, device.id)
                return [prefix]
            raise Exception(_('Account activation needed'))
        else:
            raise Exception(_('Invalid credentials'))

    @staticmethod
    def publish(payload, info, *args, **kwargs):
        if payload.get('is_list', False):
            event = {**payload.get('list')}
        else:
            results = payload.get('data', {}).split('|')
            event = {'user_id': results[0], 'status': 'online' if results[1] else 'offline'}
        return FriendOnlineSubscription(event=event)

    @classmethod
    def unsubscribed(cls, info, *args, **kwargs):
        user = info.context.user
        device = info.context.device
        if user and device:
            add_or_update_user_cache(user_id=user.id, device_id=device.id, friend_online=False)
            cls.send_notify(user_id=user.id, device_id=device.id, is_connect=False)

    @classmethod
    def send_notify(cls, user_id, device_id, is_connect=True, *args, **kwargs):
        user = UserInfo.objects.filter(user_id=user_id)
        if user.exists():
            user = user.first()
            contacts = user.contacts.split('|')
            list_online = []
            for id_user in contacts:
                user_cache = get_user_cache(id_user)
                if user_cache:
                    for device in user_cache.devices:
                        group_name = cache_prefix(FRIEND_ONLINE, id_user, device.device_id)
                        cls.broadcast(group=group_name, payload={'is_list': False, 'data': f'{id_user}|{is_connect}'})
                        if is_connect:
                            list_online.append({'user_id': id_user, 'status': 'online'})
            if is_connect:
                cls.broadcast(group=cache_prefix(FRIEND_ONLINE, user, device_id),
                              payload={'is_list': True, 'list': list_online})
        else:
            raise Exception(_('Invalid credential'))


class IncomingMessageSubscription(Subscription):
    notification_queue_limit = settings.CLIENTS_LIMIT

    # payload
    event = AutoCamelCasedScalar()

    class Arguments:
        registration_id = graphene.UUID()

    @staticmethod
    def subscribe(root, info, *args, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            device = info.context.device
            if device is None:
                device = DeviceInfo.objects.filter(registration_id=kwargs.get('registration_id'),
                                                   user_id=user.id).first()
            if user.is_authenticated and device:
                del info
                add_or_update_user_cache(user_id=user.id, device_id=device.id, incoming_msg=True)
                prefix = cache_prefix(INCOMING_MGS, user.id, device.id)
                return [prefix]
        raise Exception(_('Invalid credentials'))

    @staticmethod
    def publish(payload, info):
        return FriendOnlineSubscription(event=payload)

    @staticmethod
    def unsubscribed(cls, info, *args, **kwargs):
        user = info.context.user
        device = info.context.device
        if user and device:
            add_or_update_user_cache(user_id=user.id, device_id=device.id, incoming_msg=False)

    @classmethod
    def send_notify(cls, source: DeviceInfo, destination: DeviceInfo, message):
        receiver = get_user_cache(destination.user_id)
        if receiver:
            rec_device = receiver.find_device(destination.id)
            if rec_device and rec_device.incoming_msg:
                prefix = cache_prefix(INCOMING_MGS, destination.user_id, destination.id)
                cls.broadcast(group=prefix,
                              payload={'message': message, 'is_sync': source.user_id == destination.user_id})
        raise Exception(_('Invalid input'))


class FriendRequestSubscription(Subscription):
    # TODO: implement friend request notify
    notification_queue_limit = settings.CLIENTS_LIMIT

    # payload
    event = AutoCamelCasedScalar()

    @staticmethod
    def subscribe(root, info, *args, **kwargs):
        return

    @staticmethod
    def publish(payload, info):
        return FriendOnlineSubscription(event={'message': 'Some thing happened'})
