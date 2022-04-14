from django.conf import settings
from django_rq import job
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message as FMessage

from apps.base.mixins import Output
from apps.messenger.constants import Message
from apps.messenger.models import UserInfo, DeviceInfo
from apps.messenger.utils import validate_date_str


class UpdateAccountInfoMixin(Output):

    # _args = [phone, fist_name, last_name, dob, language, gender,discoverable_by_phone_number]
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user') and info.context.user.is_authenticated:
                user = info.context.user
                # get attrs
                phone = kwargs.get('phone', None)
                fist_name = kwargs.get('first_name', None)
                last_name = kwargs.get('last_name', None)
                dob = kwargs.get('dob', None)
                language = kwargs.get('language', None)
                gender = kwargs.get('gender', None)
                discoverable_by_phone_number = kwargs.get('discoverable_by_phone_number', None)

                is_update = False
                if phone and user.phone != phone:
                    is_update = True
                    user.phone = phone
                if fist_name and user.first_name != fist_name:
                    is_update = True
                    user.fist_name = fist_name
                if last_name and user.last_name != last_name:
                    is_update = True
                    user.last_name = last_name
                if dob and user.dob != dob:
                    is_update = True
                    user.dob = validate_date_str(dob)
                if language and user.language != language:
                    is_update = True
                    user.language = language
                if gender and settings.GENDER_CHOICE.__contains__(gender) and user.gender != gender:
                    is_update = True
                    user.gender = gender
                if discoverable_by_phone_number is not None and discoverable_by_phone_number != user.discoverable_by_phone_number:
                    is_update = True
                    user.discoverable_by_phone_number = discoverable_by_phone_number
                if is_update:
                    user.save()
                    return cls(success=True, result={'message': 'Updated successfully'})
                else:
                    return cls(success=False, errors={'message': 'No new information', 'code': 'no_info'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except ValueError as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'invalid_date'})
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})


class SendFriendRequestMixin(Output):

    # required_args = [recipient_id]
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user') and info.context.user.is_authenticated:
                user = info.context.user
                user_info = UserInfo.objects.filter(user_id=user.id).first()
                # get attrs
                recipient_id = kwargs.get('recipient_id', None)
                user_info.send_friend_request(recipient_id)
                # send notify
                cls.send_friend_request.delay(recipient_id, user.id)
                return cls(success=True, result={'message': 'Request sent'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})

    @classmethod
    @job
    def send_friend_request(cls, user_id, sender_id):
        devices = DeviceInfo.objects.filter(user_id=user_id)
        if devices.exists():
            message = FMessage(data={'type': 'friend_request', 'sender': sender_id.__str__()})
            for device in devices:
                client = FCMDevice.objects.filter(device_id=device.id, user_id=user_id).first()
                if client:
                    client.send_message(message=message)


class ProcessFriendRequestMixin(Output):
    # required_args = [sender_id, is_accept]
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user') and info.context.user.is_authenticated:
                user = info.context.user
                user_info = UserInfo.objects.filter(user_id=user.id).first()
                sender_id = kwargs.get('sender_id', None)
                is_accept = kwargs.get('is_accept', None)
                user_info.process_friend_request(user_id=sender_id, is_accept=eval(is_accept))
                if eval(is_accept):
                    cls.send_accept_signal.delay(sender_id, user.id)
                return cls(success=True, result={'message': 'Request accepted success'}) if eval(is_accept) else cls(
                    success=False, result={'message': 'Request denied success'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})

    @classmethod
    @job
    def send_accept_signal(cls, user_id, sender_id):
        devices = DeviceInfo.objects.filter(user_id=user_id)
        if devices.exists():
            message = FMessage(data={'type': 'friend_accepted', 'sender': sender_id.__str__()})
            for device in devices:
                client = FCMDevice.objects.filter(device_id=device.id, user_id=user_id).first()
                if client:
                    client.send_message(message=message)


class RemoveContactMixin(Output):

    # required_ags = [user_id]
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user') and info.context.user.is_authenticated:
                user = info.context.user
                user_info = UserInfo.objects.filter(user_id=user.id).first()
                user_info.remove_contact(kwargs.get('user_id', None))
                return cls(success=True, result={'message': 'Remove contact success'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})
