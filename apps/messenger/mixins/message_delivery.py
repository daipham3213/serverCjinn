import collections
import json
from uuid import uuid4

from django.utils import timezone
from django_rq import job
from firebase_admin.messaging import Message as FMessage, Notification
from graphene.utils.str_converters import to_camel_case
from cloudinary import CloudinaryImage, uploader

from apps.base.converter import convert_keys
from apps.base.mixins import Output
from apps.messenger.constants import Message
from apps.messenger.func import notification_sender, add_or_update_meeting, get_meeting, leave_meeting
from apps.messenger.models import DeviceInfo, Thread, MemberInfo, UserInfo, Attachment
from apps.messenger.models.redis import Calls
from apps.messenger.subscriptions import MessengerSubscription, CallSignalingSubscription


class AddThreadMixin(Output):
    # rq args = [name, member_ids, is_encrypt]
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        user, device = None, None
        try:
            if hasattr(info.context, 'user'):
                user = info.context.user
            if hasattr(info.context, 'device'):
                device = info.context.device

            name = kwargs.get('name', None)
            member_ids = kwargs.get('member_ids', [])
            is_encrypt = kwargs.get('is_encrypt', False)
            if user and device and member_ids.__len__() > 0:
                if member_ids.__len__() > 1 and is_encrypt:
                    return cls(success=False, errors={'message': 'Un-supported group encrypting'})
                thread = Thread.get_or_create_thread(thread_name=name, current_user=user, user_ids=member_ids,
                                                     is_encrypted=is_encrypt)
                if thread:
                    return cls(success=True, result={'thread_id': thread.id.__str__(), 'is_encrypted': is_encrypt,
                                                     'code': 'thread_created'})
            else:
                return cls(success=False, result=Message.INVALID_DATA_FORMAT)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})


class EditMemberMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        pass


class PromotionMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        pass


class SendMessageMixin(Output):
    #  [id, thread_id, destination_device_id, contents, reply_to, extras, created_by]
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        user, device = None, None
        if hasattr(info.context, 'user'):
            user = info.context.user
        if hasattr(info.context, 'device'):
            device = info.context.device
        if device and user:
            try:
                # getting attrs
                messages = kwargs.get('messages', None)
                files = kwargs.get('files', [])
                file_info = []

                # split by destination
                split_list = cls.split_messages(messages)
                # checking permission
                thread_list = cls.get_thread_id_list(messages)
                for thread_id in thread_list:
                    thread = Thread.objects.get(id=thread_id)
                    member_info = MemberInfo.objects.filter(
                        thread=thread, user_info__user_id=user.id).first()
                    if (not member_info or member_info.is_muted or member_info.is_blocked) and not user.is_admin:
                        return cls(success=False, errors={'message': f'{thread_id}', 'code': 'insufficient_permission'})
                        # uploading files
                    if len(files) > 0:
                        file_info = cls.file_uploading(user=user, thread_id=thread_id, files=files)

                for msgs in split_list:
                    destination_id = msgs[0].get('destination_device_id')
                    destination = DeviceInfo.objects.get(id=destination_id)
                    cls.broadcast_message.delay(device, destination, msgs, file_info)
                return cls(success=True, result={'message': 'Sending', 'time_stamp': timezone.now().__str__()})
            except Thread.DoesNotExist or DeviceInfo.DoesNotExist:
                return cls(success=False, errors=Message.INVALID_DATA_FORMAT)

            except Exception as e:
                return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})
        return cls(success=False, errors=Message.INVALID_CREDENTIAL)

    @classmethod
    @job
    def broadcast_message(cls, source: DeviceInfo, destination: DeviceInfo, messages, file_info=[]):
        message_list = []
        success = True
        file_info = json.dumps(file_info)
        # check if is sync message
        is_sync = source.user == destination.user
        for message in messages:
            # pos = message_list.items().__len__()
            message_list.append({'id': message.get('id').__str__(), 'thread_id': message.get('thread_id').__str__(),
                                 'registration_id': source.registration_id, 'media': file_info})
            message['is_sync'] = is_sync
            message['timestamp'] = timezone.now().__str__()
            sender_data = cls.get_userinfo(message.get('thread_id'), message.get('created_by'))
            message['sender'] = sender_data
            message['media'] = file_info

        method = DeviceInfo.check_device_availability(destination)
        if method == 'websocket':
            MessengerSubscription.send_notify(destination, messages)
        elif method == 'gcm' or method == 'apn':
            camel_list = []
            for message in messages:
                camel_list.append(convert_keys(message, to_camel_case))
            temp = json.dumps(camel_list)
            notification = Notification(title=f'New message from {source.user.first_name} {source.user.last_name}',
                                        body=timezone.now().__str__(), image=source.user.avatar)
            message = FMessage(data={'messages': temp, 'type': 'incoming_message'}, notification=notification)
            notification_sender(message=message, device=destination)
        else:
            success = False

        # send signal on transmit completion
        method = DeviceInfo.check_device_availability(source)
        if method == 'websocket':
            MessengerSubscription.send_completion_signal(
                source, message_list, success)
        elif method == 'gcm' or method == 'apn':
            camel_list = []
            for message in message_list:
                camel_list.append(convert_keys(message, to_camel_case))
            temp = json.dumps(camel_list)
            message = FMessage(
                data={'messages': temp, 'type': 'completion_signal', 'success': str(success)})
            notification_sender(message=message, device=source)
        else:
            raise Exception('Communication Error')

    @classmethod
    def split_messages(cls, messages):
        result = collections.defaultdict(list)
        for msg in messages:
            temp = dict(msg)
            for key, value in temp.items():
                temp[key] = value.__str__()
            result[msg['destination_device_id']].append(temp)
        return list(result.values())

    @classmethod
    def get_thread_id_list(cls, messages):
        result = []
        for msg in messages:
            if not result.__contains__(msg.get('thread_id')):
                result.append(msg.get('thread_id'))
        return result

    @classmethod
    def get_userinfo(cls, thread_id, member_id):
        try:
            member = MemberInfo.objects.filter(
                thread_id=thread_id, id=member_id).first()
            user = UserInfo.objects.filter(
                id=member.user_info.id).first().get_user()
            return {'id': user.id.__str__(), 'first_name': user.first_name, 'last_name': user.last_name,
                    'avatar': user.avatar}
        except MemberInfo.DoesNotExist:
            pass

    @classmethod
    def file_uploading(cls, user, thread_id, files=None):
        if files is None:
            files = []
        results = []
        for file in files:
            if file.content_type.__contains__('image'):
                media = uploader.upload_resource(file=file, folder=str(thread_id), tags=['attachments'],
                                                 discard_original_filename=True, eager={"width": 1920, "crop": "limit"})
                attachment = media.metadata['eager'][0]
                Attachment.objects.create(image=media, user_created=user.id, thread_id=thread_id)
                results.append({'isVideo': False, 'uri': attachment['url'], 'name': media.public_id})
            elif file.content_type.__contains__('video'):
                media = uploader.upload_large(file=file, folder=str(thread_id), tags=['attachments'],
                                              resource_type="video", discard_original_filename=True,
                                              eager={"width": 1920, "crop": "limit", "audio_codec": "none"})
                # Attachment.objects.create(video=media, user_created=user.id, thread_id=thread_id)
                results.append({'isVideo': True, 'uri': media['url'], 'name': media['public_id']})
        return results


class SeenMessageMixin(Output):

    # [message_ids] thread_id
    @classmethod
    def get_payload(cls, thread_id, message_ids):
        return {'thread_id': thread_id.__str__(), 'messages_ids': list(map(str, message_ids)), 'type': 'seen_messages'}

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        user, device = None, None
        if hasattr(info.context, 'user'):
            user = info.context.user
        if hasattr(info.context, 'device'):
            device = info.context.device
        try:
            if user and device:
                thread = Thread.objects.filter(members__user_info__user_id=user.id, id=kwargs.get('thread_id')).first()
                payload = cls.get_payload(thread.id, kwargs.get('message_ids', []))
                # getting list members
                user_id_list = thread.get_user_ids().append(user.id)
                # getting list devices of members
                other_devices = DeviceInfo.objects.filter(
                    user__in=user_id_list).exclude(id=device.id)
                # sending seen signal
                for candidate in other_devices:
                    if candidate.is_enabled():
                        cls.broadcast_signal(candidate, payload)
                return cls(success=True, result={'message': 'Signal broadcast success', 'code': 'seen_signal_sent'})
        except Thread.DoesNotExist:
            return cls(success=False, errors={'message': 'Invalid thread', 'code': 'invalid_thread'})

    @classmethod
    @job
    def broadcast_signal(cls, device, payload):
        method = DeviceInfo.check_device_availability(device)
        if method == 'websocket':
            MessengerSubscription.send_seen_signal(device, payload)
        elif method == 'gcm':
            message = Message(data=payload, topic='seen_signal_sent')
            notification_sender(message=message, device=device)
        elif method == 'apn':
            pass


# <editor-fold>
class CallSignalingMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user') and hasattr(info.context, 'device'):
                user = info.context.user
                user_info = UserInfo.objects.get(user_id=user.id)
                contacts = user_info.get_contacts()
                # checking contacts
                callee_id = kwargs.get('user_id', None)
                # if not contacts.__contains___(str(callee_id)):
                #     return cls(success=False, errors={'message': 'Invalid contact', 'code': 'invalid_id'})

                cls.send_call_signal.delay(user, callee_id, kwargs.get('meeting_id'))
                return cls(success=True, result={'message': 'success'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})

    @classmethod
    @job
    def send_call_signal(cls, source, destination, meeting_id, data=None):
        meeting_id = str(meeting_id)
        payload = {
            'signal_type': 'calling',
            'from': {
                'id': source.id.__str__(),
                'first_name': source.first_name,
                'last_name': source.last_name,
                'username': source.username,
            },
            'meeting_id': meeting_id,
        }
        notification = Notification(title=f'Incoming call from {source.first_name} {source.last_name}',
                                    image=source.avatar)

        temp = json.dumps(convert_keys(payload, to_camel_case))
        message = FMessage(notification=notification, data={
            'type': 'meeting',
            'payload': temp,
        })
        for device in DeviceInfo.objects.filter(user_id=destination):
            notification_sender(message=message, device=device)


# </editor-fold>

class CallSignaling2Mixin(Output):

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user') and hasattr(info.context, 'device'):
                user = info.context.user

                # signal type, has_video, call_id, recipients, answer, offer
                signal_type = kwargs.get('signal_type', None)
                call_id = kwargs.get('call_id', None)

                if signal_type == 'add_offer_candidate':
                    offer_candidate = kwargs.get('offer_candidate')
                    if not call_id:
                        has_video = kwargs.get('has_video', True)
                        pk, call = Calls.create_call(offer_candidate=offer_candidate, has_video=has_video)
                        return cls(success=True, result={'call_id': pk})
                    if call_id:
                        update = Calls.update_call(call_id=call_id, offer_candidate=offer_candidate)
                        if update:
                            CallSignalingSubscription.broadcast(group=cls.prefix(call_id),
                                                                payload={'signal_type': signal_type,
                                                                         'offer_candidate': offer_candidate})
                            return cls(success=True, results={'call_id': call_id})
                        else:
                            return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
                if signal_type == 'add_answer_candidate':
                    answer_candidate = kwargs.get('answer_candidate')
                    if not call_id:
                        return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
                    update = Calls.update_call(call_id, answer_candidate=answer_candidate)
                    if update:
                        CallSignalingSubscription.broadcast(group=cls.prefix(call_id),
                                                            payload={'signal_type': signal_type,
                                                                     'answer_candidate': answer_candidate})
                        return cls(success=True, results={'call_id': call_id})
                    else:
                        return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
                if signal_type == 'offer' or signal_type == 'answer':
                    offer = kwargs.get(signal_type, None)
                    to = kwargs.get('to', None)
                    if not offer or not to:
                        return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
                    update = Calls.update_call(call_id, offer=offer)
                    if update:
                        payload = {
                            'signal_type': signal_type,
                            'call_id': call_id,
                            'data': offer,
                        }
                        cls.send_signal.delay(user, to, payload)
                        return cls(success=True, result={'call_id': call_id})
                    else:
                        return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
                if signal_type == 'denied' or signal_type == 'busy':
                    if not call_id:
                        return cls(success=False, errors=Message.INVALID_DATA_FORMAT)
                    payload = {
                        'signal_type': signal_type,
                        'call_id': call_id,
                    }
                    Calls.stop_call(call_id)
                    cls.send_signal(user, '', payload)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})

    @classmethod
    def prefix(cls, meeting_id):
        return f'meeting:{meeting_id.__str__()}'

    @classmethod
    @job
    def send_signal(cls, source, destination, data):
        data['from'] = {
            'id': source.id.__str__(),
            'first_name': source.first_name,
            'last_name': source.last_name,
            'username': source.username,
        }
        if data['signal_type'] == 'offer':
            notification = Notification(title=f'Incoming call from {source.first_name} {source.last_name}',
                                        image=source.avatar)

            temp = json.dumps(convert_keys(data, to_camel_case))
            message = FMessage(notification=notification, data={
                'type': 'meeting',
                'payload': temp,
            })
            for device in DeviceInfo.objects.filter(user_id=destination):
                notification_sender(message=message, device=device)
        else:
            CallSignalingSubscription.broadcast(group=cls.prefix(data['id']), payload=data)
