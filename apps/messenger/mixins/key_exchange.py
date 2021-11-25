import datetime
import logging
from builtins import Exception

import pytz
from django.conf import settings
from django.utils import timezone

from apps.auths.models import Token
from apps.base.mixins import Output
from apps.base.utils import format_message
from apps.log.func import authorization_log, activity_log
from apps.messenger.constants import Message
from apps.messenger.exceptions import PreKeyBundleError, PreKeyCountExceededError, SignedPreKeyInvalid, \
    DeviceLimitExceed
from apps.messenger.models import DeviceInfo, SignedPreKey, PreKey

logger = logging.getLogger(__name__)

utc = pytz.UTC


class AddSignedPreKeyMixin(Output):
    @classmethod
    def validate(cls, user, registration_id):
        if (user or registration_id) is None:
            raise SignedPreKeyInvalid()
        device = DeviceInfo.objects.filter(user=user, registrationId=registration_id).first()
        if device is None:
            raise SignedPreKeyInvalid()
        return device

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user'):
                user = info.context.user
                registration_id = int(kwargs.get('registrationId'))
                device = cls.validate(user, registration_id)
                device.signed_pre_key.delete()

                SignedPreKey.objects.create(device=device, **kwargs)
                return cls(success=False, result={'details': 'Signed pre-key created successfully'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except SignedPreKeyInvalid:
            return cls(success=False, errors=Message.INVALID_SIGNED_PRE_KEY)
        except Exception as e:
            return cls(success=False, errors={'message': e, 'code': 'unexpected_exception'})


class AddKeyBundleMixin(Output):
    @classmethod
    def validate(cls, pre_keys, signed_pre_key, identity_key, device, user):
        is_update = False

        if (pre_keys and user and device) is None:
            raise PreKeyBundleError()

        if device.signed_pre_key is None or (signed_pre_key.public_key != device.signed_pre_key.public_key
                                             and signed_pre_key.signature != device.signed_pre_key.signature
                                             and signed_pre_key.key_id != device.signed_pre_key.id):
            is_update = True
        if identity_key != user.identity_key:
            is_update = True

        if is_update:
            pass
        else:
            raise PreKeyBundleError()

    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user'):
                user = info.context.user
                device = DeviceInfo.objects.filter(registration_id=int(kwargs.get('registration_id')),
                                                   user=user).first()
                pre_keys = kwargs.get('pre_keys')
                signed_pre_key = kwargs.get('signed_pre_key')
                identity_key = kwargs.get('identity_key')

                cls.validate(pre_keys, signed_pre_key, identity_key, device, user)

                for pre_key in pre_keys:
                    PreKey.objects.create(id=int(pre_key.key_id), public_key=pre_key.public_key,
                                          device_id=device.id)

                device.signed_pre_key = SignedPreKey.objects.create(id=signed_pre_key.key_id,
                                                                    public_key=signed_pre_key.public_key,
                                                                    signature=signed_pre_key.signature)
                user.identity_key = identity_key
                user.date_modified = timezone.now()
                device.save()
                user.save()
                activity_log(user=user.id, remarks='Update key bundle', doc_id=device.id, date_created=timezone.now(),
                             data={'user_id': user.id, 'device_id': device.id})
                return cls(success=True, result={'details': 'Key bundle updated success.'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except PreKeyBundleError:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
            return cls(success=False, errors=Message.INVALID_PRE_KEY_BUNDLE)
        except PreKeyCountExceededError:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
            return cls(success=False, errors=Message.PRE_KEY_COUNT_EXCEEDED)
        except Exception as e:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 500))
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})


class CreateDeviceTokenMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user') and info.context.user.is_authenticated:
                user = info.context.user
                if DeviceInfo.get_enable_device_count(user) > settings.DEVICE_LIMIT:
                    return cls(success=False, errors=Message.DEVICE_LIMIT_EXCEED)

                data = {'verify_device': True, 'registration_id': kwargs.get('registrationId'), }
                token = Token.create_otp(account=user.email, username=user.username, is_valid=True, data=data)
                token.data = data
                token.is_valid = True
                token.save()
                if token:
                    result = {
                        'verify_id': token.id,
                        'created_at': token.date_created.replace(tzinfo=utc),
                        'expire_in': settings.LOGIN_OTP_EXPIRE
                    }
                    logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 200))
                    return cls(success=True, result=result)
                else:
                    logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
                    return cls(success=False, errors=Message.INVALID_CREDENTIAL)
            else:
                logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except Exception as e:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 500))
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})


class VerifyDeviceTokenMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user'):
                user = info.context.user
                if DeviceInfo.get_enable_device_count(user) > settings.DEVICE_LIMIT:
                    raise DeviceLimitExceed()
                # get attributes
                password = kwargs.get('password')
                registration_id = kwargs.get('registrationId')
                otp = kwargs.get('otp')
                # get device info
                device_name = kwargs.get('deviceName')

                data = {'verify_device': True, 'registration_id': registration_id, }
                token = Token.objects.filter(username=user.username, otp=otp, data=data).first()
                if token:
                    if token.is_valid:
                        time_difference = datetime.datetime.now() - datetime.timedelta(
                            hours=getattr(settings, 'EXPIRE_VALID_USER', 24))
                    else:
                        time_difference = datetime.datetime.now() - datetime.timedelta(
                            minutes=getattr(settings, 'LOGIN_OTP_EXPIRE', 15))
                    if token.date_created >= time_difference:
                        device = DeviceInfo.create(user=user, password=password,
                                                   registration_id=int(registration_id), name=device_name)
                        if device:
                            token.delete()
                            authorization_log(user, 'Add new device',
                                              {'registration_id': registration_id, 'device_name': device_name})
                            return cls(success=True,
                                       result={'device_id': device.id.__str__(), 'registration_id': registration_id,
                                               'device_token': device.token})
                return cls(success=False, errors=[{'message': 'Invalid OTP', 'code': 'invalid_otp'}])
            else:
                logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 400))
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except Exception as e:
            logger.info(format_message(cls, info.context.method, 'no_status', '', '', info.context.body, 500))
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})


class RemoveDeviceMixin(Output):
    @classmethod
    def resolve_mutation(cls, root, info, **kwargs):
        try:
            if hasattr(info.context, 'user'):
                user = info.context.user
                registration_id = int(kwargs.get('registration_id'))

                if registration_id is None:
                    return cls(sucess=False, errors=Message.INVALID_DATA_FORMAT)
                device = DeviceInfo.objects.filter(registration_id=registration_id, user=user)
                if device is None:
                    return cls(success=False, errors=Message.INVALID_CREDENTIAL)
                device.delete()
                return cls(success=True, result={'message': 'Successfully remove device.'})
            else:
                return cls(success=False, errors=Message.INVALID_CREDENTIAL)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})


class UpdateDeviceInfoMixin(Output):

    # args = [gcm_id, apn_id, void_apn_id]
    # response result
    @classmethod
    def resolve_mutation(cls, roo, info, **kwargs):
        try:
            if hasattr(info.context, 'device'):
                device: DeviceInfo = info.context.device
                gcm_id = kwargs.get('gcm_id', None)
                apn_id = kwargs.get('apn_id', None)
                void_apn_id = kwargs.get('void_apn_id', None)

                is_update = False
                if device.gcm_id != gcm_id and gcm_id:
                    device.gcm_id = gcm_id
                    is_update = True
                if device.apn_id != apn_id and apn_id:
                    device.apn_id = apn_id
                    is_update = True
                if device.void_apn_id != void_apn_id and void_apn_id:
                    device.void_apn_id = void_apn_id
                    is_update = True
                if is_update:
                    device.save()
                    return cls(success=True, result={'message': 'Update device info success'})
                raise Exception('No new info to update')
            else:
                return cls(success=False, errors=Message.NO_AUTH_DEVICE)
        except Exception as e:
            return cls(success=False, errors={'message': e.__str__(), 'code': 'unexpected_exception'})
