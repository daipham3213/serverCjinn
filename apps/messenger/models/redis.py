from django.conf import settings
from django.core.cache import cache


class DeviceServices:
    device_id = ''
    friend_online = False
    incoming_msg = False

    def __init__(self, device_id: str, friend_online=False, incoming_msg=False):
        self.device_id = device_id
        self.friend_online = friend_online
        self.incoming_msg = incoming_msg


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

    def add_or_update_device(self, device_id: str, friend_online=None, incoming_msg=None):
        if self.find_device(device_id) is None:
            friend_online = False if friend_online is None else friend_online
            incoming_msg = False if incoming_msg is None else incoming_msg
            self.devices.append(DeviceServices(device_id, friend_online, incoming_msg))
        else:
            if incoming_msg is not None:
                self.find_device(device_id).incoming_msg = incoming_msg
            if friend_online is not None:
                self.find_device(device_id).friend_online = friend_online
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
