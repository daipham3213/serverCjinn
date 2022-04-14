import json
import uuid
from re import S
from django.conf import settings
from django.core.cache import cache


class DeviceServices:
    device_id = ''
    friend_online = False
    incoming_msg = False
    requests = False
    thread_id = None

    def __init__(self, device_id: str, friend_online=False, incoming_msg=False, request=False, thread_id=None):
        self.device_id = device_id
        self.friend_online = friend_online
        self.incoming_msg = incoming_msg
        self.requests = request
        self.thread_id = thread_id


class Subscriber:
    devices: list[DeviceServices] = []

    def __init__(self, devices=None):
        if devices is None:
            devices = []
        self.devices = devices

    def find_device(self, device_id: str):
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None

    def add_or_update_device(self, device_id: str, friend_online=None, incoming_msg=None, request=None, thread_id=None):
        if self.find_device(device_id) is None:
            friend_online = False if friend_online is None else friend_online
            incoming_msg = False if incoming_msg is None else incoming_msg
            request = False if request is None else request
            self.devices.append(DeviceServices(device_id, friend_online, incoming_msg, request, thread_id))
        else:
            if incoming_msg is not None:
                self.find_device(device_id).incoming_msg = incoming_msg
            if friend_online is not None:
                self.find_device(device_id).friend_online = friend_online
            if request is not None:
                self.find_device(device_id).requests = request
            self.find_device(device_id).thread_id = thread_id
        return self

    def remove_device(self, device_id: str):
        device = self.find_device(device_id)
        if device:
            self.devices.remove(device)
            if self.devices.__len__() == 0:
                del self
            return True
        return False


class Mailbox:
    device_id = ''
    message_queue = []

    def __init__(self, device_id):
        self.device_id = device_id.__str__()

    def insert_queue(self, task_id):
        if self.queue_count() > settings.MESSAGE_QUEUE_LIMIT:
            item_id = self.message_queue.pop(0)
            # TODO: remove task

        self.message_queue.append(task_id)

    def remove_task(self, task_id):
        self.message_queue.remove(task_id)
        # TODO: remove task

    def queue_count(self):
        return self.message_queue.__len__()

    @classmethod
    def get_or_create_device_mailbox(cls, device_id):
        prefix = f'mailbox_{device_id.__str__()}'
        mailbox = cache.get(prefix)
        if mailbox is None:
            mailbox = Mailbox(device_id)
            cache.set(prefix, mailbox)
        return mailbox

    def save(self):
        prefix = f'mailbox_{self.device_id.__str__()}'
        if self.queue_count() == 0:
            return self.remove()
        return cache.set(prefix, self)

    def remove(self):
        prefix = f'mailbox_{self.device_id.__str__()}'
        return cache.delete(prefix)


class Meeting:
    caller = {}
    callee = []

    def __init__(self, caller):
        self.caller = caller

    def add_callee(self, callee):
        self.callee.append(callee)

    def stop_meeting(self):
        del self

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Calls:
    offer = {}
    answer = {}
    offer_candidates = []
    answer_candidates = []
    has_video = True

    def __init__(self, offer_candidate, has_video=True):
        self.offer_candidates.append(offer_candidate)
        self.has_video = has_video

    @classmethod
    def generate_id(cls):
        return uuid.uuid4().__str__()

    @classmethod
    def call_prefix(cls, call_id):
        return f'call:{call_id.__str__()}'

    @classmethod
    def get_call(cls, call_id):
        return cache.get(cls.call_prefix(call_id))

    @classmethod
    def create_call(cls, offer_candidate, has_video):
        call = Calls(offer_candidate, has_video)
        pk = cls.generate_id()
        cache.set(pk, call)
        return pk, call

    @classmethod
    def stop_call(cls, call_id):
        prefix = cls.call_prefix(call_id)
        cache.delete(prefix)

    @classmethod
    def update_call(cls, call_id, offer_candidate=None, answer_candidate=None, answer=None, offer=None):
        call: Calls = cls.get_call(call_id)
        update = False
        if not call:
            raise ValueError('Invalid call')
        if offer_candidate and not call.offer_candidates.__contains__(offer_candidate):
            call.offer_candidates.append(offer_candidate)
            update = True
        if answer_candidate and not call.answer_candidates.__contains__(answer_candidate):
            call.answer_candidates.append(answer_candidate)
            update = True
        if answer and call.answer != answer:
            call.answer = answer
            update = True
        if offer and call.offer != offer:
            call.offer = offer
            update = True
        if update:
            cache.set(cls.call_prefix(call_id), call)
        return update