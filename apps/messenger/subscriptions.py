import graphene
from channels_graphql_ws import Subscription
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.base.converter import AutoCamelCasedScalar
from apps.messenger.constants import FRIEND_ONLINE, INCOMING_MGS, FRIEND_REQUEST, PRIVATE_CHANNEL
from apps.messenger.func import cache_prefix, get_user_cache, add_or_update_user_cache, get_meeting
from apps.messenger.mixins.subscription import AuthenticationMixin
from apps.messenger.models import UserInfo, DeviceInfo
from apps.messenger.models.message_thread import MemberInfo, Thread
from apps.messenger.types import OnlineEvent, MessageEventType


class FriendOnlineSubscription(Subscription, AuthenticationMixin):
    notification_queue_limit = settings.CLIENTS_LIMIT

    # payload
    event = graphene.Field(OnlineEvent)

    @classmethod
    def resolve_subscribe(cls, info, *args, **kwargs):
        user = kwargs.get('user', None)
        device = kwargs.get('device', None)
        add_or_update_user_cache(
            user_id=user.id, device_id=device.id, friend_online=True)
        prefix = cache_prefix(FRIEND_ONLINE, user.id, device.id)
        cls.send_notify(user.id, device.id, True)
        return [prefix]

    @staticmethod
    def publish(payload, info, *args, **kwargs):
        if payload.get('is_list', False):
            event = {**payload.get('list')}
        else:
            results = payload.get('data', {}).split('|')
            status = 'offline'
            if results[1] == 'True':
                status = 'online'
            event = {'user_id': results[0], 'status': status}
        return FriendOnlineSubscription(event={**event})

    @classmethod
    def unsubscribed(cls, info, *args, **kwargs):
        if args.__len__() > 0 and hasattr(args[0], 'context'):
            context = args[0].context
        else:
            context = info.context
        user = context.user
        device = context.device
        if user and device:
            add_or_update_user_cache(
                user_id=user.id, device_id=device.id, friend_online=False)
            cls.send_notify(user_id=user.id,
                            device_id=device.id, is_connect=False)

    @classmethod
    def send_notify(cls, user_id, device_id, is_connect=True, *args, **kwargs):
        user = UserInfo.objects.filter(user_id=user_id).first()
        if user:
            contacts = user.get_contacts()
            # list_online = []
            for id_user in contacts:
                user_cache = get_user_cache(id_user)
                if user_cache:
                    for device in user_cache.devices:
                        group_name = cache_prefix(
                            FRIEND_ONLINE, id_user, device.device_id)
                        cls.broadcast(group=group_name, payload={
                            'is_list': False, 'data': f'{id_user}|{is_connect}'})
            #             if is_connect:
            #                 list_online.append({'user_id': id_user, 'status': 'online'})
            # if is_connect:
            #     cls.broadcast(group=cache_prefix(FRIEND_ONLINE, user, device_id),
            #                   payload={'is_list': True, 'list': list_online})
        else:
            raise Exception(_('Invalid credential'))


class MessengerSubscription(Subscription, AuthenticationMixin):
    notification_queue_limit = settings.CLIENTS_LIMIT

    # payload
    event = graphene.Field(MessageEventType, required=True)

    @classmethod
    def resolve_subscribe(cls, info, *args, **kwargs):
        user = kwargs.get('user', None)
        device = kwargs.get('device', None)
        add_or_update_user_cache(
            user_id=user.id, device_id=device.id, incoming_msg=True)
        prefix = cache_prefix(INCOMING_MGS, user.id, device.id)
        device.fetches_messages = True
        device.save()
        return [prefix]

    @staticmethod
    def publish(payload, info):
        temp = payload  # json.dumps(payload)
        return MessengerSubscription(event={**temp})

    @staticmethod
    def unsubscribed(root, info, *args, **kwargs):
        if args.__len__() > 0 and hasattr(args[0], 'context'):
            context = args[0].context
        else:
            context = info.context
        user = context.user
        device = context.device
        if user and device:
            add_or_update_user_cache(
                user_id=user.id, device_id=device.id, incoming_msg=False)
            device.fetches_messages = False
            device.save()

    @classmethod
    def send_notify(cls, destination: DeviceInfo, message):
        receiver = get_user_cache(destination.user_id)
        if receiver:
            device = receiver.find_device(destination.id.__str__())
            if device and not device.thread_id:
                prefix = cache_prefix(
                    INCOMING_MGS, destination.user_id, destination.id)
                cls.broadcast(group=prefix, payload={
                    'data': message, 'type': 'incoming_message'})
            elif device and device.thread_id:
                prefix = f'{PRIVATE_CHANNEL}:{device.thread_id}'
                PrivateChannelSubscription.broadcast(group=prefix,
                                                     payload={'data': message, 'type': 'incoming_message'})
        else:
            raise Exception(_('Invalid input'))

    @classmethod
    def send_completion_signal(cls, destination: DeviceInfo, payload, success=True):
        receiver = get_user_cache(destination.user_id)
        if receiver:
            device = receiver.find_device(destination.id.__str__())
            if device:
                prefix = cache_prefix(
                    INCOMING_MGS, destination.user_id, destination.id)
                cls.broadcast(group=prefix, payload={
                    'type': 'completion_signal', 'data': payload, 'success': success})
            elif device and device.thread_id:
                prefix = f'{PRIVATE_CHANNEL}:{device.thread_id}'
                PrivateChannelSubscription.broadcast(group=prefix,
                                                     payload={'data': payload, 'type': 'completion_signal'})
        else:
            raise Exception(_('Invalid input'))

    @classmethod
    def send_seen_signal(cls, destination: DeviceInfo, payload):
        receiver = get_user_cache(destination.user_id)
        if receiver:
            device = receiver.find_device(destination.id.__str__())
            if device:
                prefix = cache_prefix(
                    INCOMING_MGS, destination.user_id, destination.id)
                cls.broadcast(group=prefix, payload={
                    'type': 'seen_signal', 'data': payload})
            elif device and device.thread_id:
                prefix = f'{PRIVATE_CHANNEL}:{device.thread_id}'
                PrivateChannelSubscription.broadcast(
                    group=prefix, payload={'data': payload, 'type': 'seen_signal'})
        else:
            raise Exception(_('Invalid input'))


class FriendRequestSubscription(Subscription, AuthenticationMixin):
    # TODO: implement friend request notify
    notification_queue_limit = settings.CLIENTS_LIMIT

    # payload
    event = AutoCamelCasedScalar()

    @classmethod
    def resolve_subscribe(cls, info, *args, **kwargs):
        user = kwargs.get('user', None)
        device = kwargs.get('device', None)
        add_or_update_user_cache(
            user_id=user.id, device_id=device.id, request=True)
        prefix = cache_prefix(FRIEND_REQUEST, user.id, device.id)
        return [prefix]

    @staticmethod
    def publish(payload, info):
        return FriendRequestSubscription(event=payload)

    @classmethod
    def send_notify(cls, sender_id, receiver_id):
        receiver = get_user_cache(receiver_id)
        if receiver:
            for device in receiver.devices:
                prefix = cache_prefix(
                    FRIEND_REQUEST, receiver_id, device.device_id)
                cls.broadcast(group=prefix, payload={'sender': sender_id})
        else:
            devices = DeviceInfo.objects.filter(user_id=receiver_id)
            for device in devices:
                client = None
        # send notify


class PrivateChannelSubscription(Subscription, AuthenticationMixin):
    event = graphene.Field(MessageEventType, required=True)

    @classmethod
    def resolve_subscribe(cls, info, *args, **kwargs):
        user = kwargs.get('user', None)
        device = kwargs.get('device', None)
        thread_id = kwargs.get('thread_id', None)
        try:
            if user and device and thread_id:
                member = MemberInfo.objects.filter(
                    thread_id=thread_id, user_info__user_id=user.id).first()
                if not member.is_blocked:
                    add_or_update_user_cache(user_id=user.id, device_id=device.id, incoming_msg=True,
                                             thread_id=thread_id)
                    return [f'{PRIVATE_CHANNEL}:{thread_id.__str__()}']
                raise Exception('Insufficient Permission')
        except Thread.DoesNotExist:
            raise Exception('Invalid input')

    @staticmethod
    def publish(payload, info):
        return PrivateChannelSubscription(event={**payload})

    @staticmethod
    def unsubscribed(root, info, *args, **kwargs):
        if args.__len__() > 0 and hasattr(args[0], 'context'):
            context = args[0].context
        else:
            context = info.context
        user = context.user
        device = context.device
        if user and device:
            add_or_update_user_cache(
                user_id=user.id, device_id=device.id, thread_id=None)


class CallSignalingSubscription(Subscription):
    event = AutoCamelCasedScalar()

    class Arguments:
        meeting_id = graphene.UUID(required=True)

    @staticmethod
    def subscribe(root, info, meeting_id):
        if hasattr(info.context, 'user') and hasattr(info.context, 'device'):
            meeting = get_meeting(meeting_id)
            if meeting:
                return [f'meeting:{meeting_id.__str__()}']
        else:
            raise Exception(_('Invalid credentials'))

    @staticmethod
    def publish(payload, info, meeting_id):
        print('broadcasting ', payload)
        return CallSignalingSubscription(event={'data': payload})

    @staticmethod
    def unsubscribed(root, info, meeting_id):
        # if args.__len__() > 0 and hasattr(args[0], 'context'):
        #     context = args[0].context
        # else:
        context = info.context
        user = context.user
        if user:
            payload = {
                'signal_type': 'left',
                'from': {
                    'id': user.id.__str__(),
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                }
            }
            CallSignalingSubscription.broadcast(group=f'meeting:{meeting_id.__str__()}', payload=payload)
