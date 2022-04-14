from django.conf import settings
from django.core.cache import cache
from fcm_django.models import FCMDevice

from apps.messenger.models.redis import Meeting, Subscriber, Calls

api = 'https://fcm.googleapis.com/fcm/send'


def cache_prefix(service_name, user_id, device_id):
    return f'{service_name}:{user_id.__str__()}:{device_id.__str__()}'


def get_user_cache(user_id):
    user: Subscriber = cache.get(user_id.__str__())
    return user


def add_or_update_user_cache(user_id, device_id=None, friend_online=None, incoming_msg=None, request=None,
                             thread_id=None):
    user: Subscriber = cache.get(user_id.__str__())
    if user is None:
        user = Subscriber()
    if device_id:
        user.add_or_update_device(device_id=device_id.__str__(), friend_online=friend_online, incoming_msg=incoming_msg,
                                  request=None, thread_id=thread_id)
    return cache.set(user_id, user, timeout=settings.CACHE_TIMEOUT)


def remove_user_cache(user_id, device_id=None):
    if device_id:
        user = get_user_cache(user_id)
        if user:
            user.remove_device(device_id=device_id.__str__())
            if user.devices.__len__() > 0:
                cache.set(user_id.__str__(), user,
                          timeout=settings.CACHE_TIMEOUT)
            else:
                cache.delete(user_id.__str__())
    else:
        cache.delete(user_id.__str__())


def notification_sender(message, device):
    fcm_client = FCMDevice.objects.filter(
        device_id=device.id.__str__(), user_id=device.user_id).first()
    if fcm_client:
        fcm_client.send_message(message=message)
    else:
        raise Exception('Device not found')


def meeting_prefix(meeting_id):
    return f'meeting:{meeting_id.__str__()}'


def get_meeting(meeting_id):
    meeting: Meeting = cache.get(meeting_prefix(meeting_id))
    return meeting


def add_or_update_meeting(meeting_id, caller, callees=[]):
    meeting = get_meeting(meeting_id)
    if not meeting:
        meeting = Meeting(caller)
    if len(callees) > 0:
        for i in range(len(callees)):
            meeting.add_callee(callees[i])
    cache.set(meeting_prefix(meeting_id), meeting)
    return meeting


def leave_meeting(meeting_id, callee_id):
    meeting = get_meeting(meeting_id)
    if meeting and meeting.caller['id'] == callee_id.__str__():
        cache.delete(meeting_id.__str__())
    if meeting:
        meeting.callee = [callee for callee in meeting.callee if callee['id'] != callee_id.__str__()]
        if len(meeting.callee) == 0:
            cache.delete(meeting_id.__str__())
        else:
            return add_or_update_meeting(meeting_id, meeting.caller, meeting.callee)
