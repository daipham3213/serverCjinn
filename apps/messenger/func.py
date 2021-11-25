from django.core.cache import cache

from apps.messenger.models.redis import Subscriber

api = 'https://fcm.googleapis.com/fcm/send'


def cache_prefix(service_name, user_id, device_id):
    return f'{service_name}:{user_id.__str__()}:{device_id.__str__()}'


def get_user_cache(user_id):
    user: Subscriber = cache.get(user_id.__str__())
    return user


def add_or_update_user_cache(user_id, device_id=None, friend_online=None, incoming_msg=None):
    user: Subscriber = cache.get(user_id.__str__())
    if user is None:
        user = Subscriber()
    if device_id:
        user.add_or_update_device(device_id=device_id.__str__(), friend_online=friend_online, incoming_msg=incoming_msg)
    return cache.set(user_id, user, timeout=None)


def remove_user_cache(user_id, device_id=None):
    if device_id:
        user = get_user_cache(user_id)
        user.remove_device(device_id=device_id.__str__())
        if user.devices.__len__() > 0:
            cache.set(user_id.__str__(), user, timeout=None)
        else:
            cache.delete(user_id.__str__())
    else:
        cache.delete(user_id.__str__())


def notification_sender():
    pass
