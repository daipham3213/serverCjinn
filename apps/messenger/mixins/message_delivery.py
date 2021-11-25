from django_rq import job
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message

from apps.base.mixins import Output
from apps.messenger.constants import Message
from apps.messenger.func import get_user_cache
from apps.messenger.models import DeviceInfo, Thread, Message as ThreadMessage
from apps.messenger.subscriptions import IncomingMessageSubscription


class AddThreadMixin(Output):
    # rq args = [name, member_ids, is_encrypt]
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        user = None
        device = None
        try:
            if hasattr(info.context, 'user'):
                user = info.context.user
            if hasattr(info.context, 'device'):
                device = info.context.device

            name = kwargs.get('name', None)
            member_ids = kwargs.get('member_ids', [])
            is_encrypt = kwargs.get('is_encrypt', False)
            if user and device and name and member_ids.__len__() > 1:
                if member_ids.__len__() > 1 and is_encrypt:
                    return cls(success=False, errors={'message': 'Un-supported group encrypting'})
                thread = Thread.add_member_or_create(thread_name=name, current_user=user, user_ids=member_ids,
                                                     is_encrypt=is_encrypt)
                if thread:
                    return cls(success=True,
                               result={'message': 'Action complete successfully', 'code': 'thread_created'})
            else:
                return cls(success=False, result=Message.INVALID_DATA_FORMAT)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})


class ThreadEditMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        pass


class SendMessageMixin(Output):

    # rq_args = [thread, msg]
    # args = [registration_id, reply_to]
    @classmethod
    def resolve(cls, root, info, **kwargs):
        user = None
        device = None
        if hasattr(info.context, 'user'):
            user = info.context.user
        if hasattr(info.context, 'device'):
            device = info.context.device
        elif user:
            device = DeviceInfo.objects.filter(user=user, registration_id=kwargs.get('registration_id'))

        if device and user:
            # getting attrs
            thread_id = kwargs.get('thread_id', None)
            contents = kwargs.get('contents', None)

            reply_to = kwargs.get('reply_to', None)
            extras = kwargs.get('extras', {})
            try:
                if thread_id and contents:
                    thread = Thread.objects.get(id=thread_id)
                    if thread.get_member_ids().__contains__(user.id):
                        message = ThreadMessage.objects.create(thread=thread, contents=contents, reply_to=reply_to,
                                                               extras=extras, user_created=user.id)
                        if not thread.is_group():
                            task = cls.broadcast_message(device, message, thread.is_encrypted)
                        else:
                            task = cls.broadcast_group_message(device, message)
                    return cls(success=True, result={'task_id': task.id})
                return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
            except Thread.DoesNotExist:
                return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
            except Exception as e:
                return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})
            # transfer to members
            # sync devices

    @classmethod
    @job
    def broadcast_message(cls, sender_device: DeviceInfo, message: ThreadMessage, is_encrypted: bool):
        # sync
        sender_id = message.user_created
        if not is_encrypted:
            sender_devices = DeviceInfo.objects.filter(user_id=sender_id).exclude(id=sender_device.id)
            for device in sender_devices:
                cls.send_message(sender_device, device, message)
            # broadcast
        receivers = message.thread.get_user_ids()
        rec_device = DeviceInfo.objects.filter(user_id=receivers[0]).first()
        cls.send_message(sender_device, rec_device, message)

    @classmethod
    @job
    def broadcast_group_message(cls, sender_device: DeviceInfo, message: ThreadMessage):
        pass

    @classmethod
    def check_device_availability(cls, device: DeviceInfo):
        if not device.apn_id and not device.gcm_id and not get_user_cache(device.user_id):
            raise Exception('Unable to communicate with receiver')
        method = ''
        if device.fetches_messages and get_user_cache(device.user_id):
            method = 'websocket'
        elif device.gcm_id:
            method = 'gcm'
        elif device.apn_id:
            method = 'apn'

        return method

    @classmethod
    def send_message(cls, source: DeviceInfo, destination: DeviceInfo, message: ThreadMessage):
        method = cls.check_device_availability(destination)
        if method == 'websocket':
            IncomingMessageSubscription.send_notify(source, destination, message)
        elif method == 'gcm':
            client, created = FCMDevice.objects.get_or_create(registration_id=destination.gcm_id, name=destination.name,
                                                              user_id=destination.user_id, device_id=destination.id)
            message = Message(data=message, topic=f'New message from {source.user.name}')
            client.send_message(message=message)
        elif method == 'apn':
            pass
