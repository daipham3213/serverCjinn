import graphene

from apps.messenger.models import PreKey, DeviceInfo
from apps.messenger.types.keys import PreKeyCount, PreKeyResponseType, PreKeyItemType, SignedPreKeyType


class KeyQuery(graphene.ObjectType):
    get_status = graphene.Field(PreKeyCount, device_id=graphene.UUID())
    get_device_keys = graphene.Field(PreKeyResponseType, device_id=graphene.String())
    get_signed_pre_key = graphene.Field(SignedPreKeyType, device_id=graphene.UUID())

    @staticmethod
    def resolve_get_status(root, info, device_id, **kwargs):
        if hasattr(info.context, 'user'):
            counted = PreKey.objects.filter(device_id=device_id).count()
            return PreKeyCount(count=counted)
        return None

    @staticmethod
    def resolve_get_signed_pre_key(root, info, device_id, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            device = DeviceInfo.objects.filter(user=user, id=device_id).first()
            if device and device.signed_pre_key:
                return device.signed_pre_key
        return None

    @staticmethod
    def resolve_get_device_keys(root, info, device_id, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            devices = DeviceInfo.objects.filter(user=user)
            items = []
            if devices.count() > 0:
                for device in devices:
                    if device.is_enabled() and (
                            device_id == '*' or device_id == device.id.__str__()) and device.prekey_set.count() > 0:
                        signed_key = device.signed_pre_key
                        pre_key = device.prekey_set.all()[:1].get()
                        if signed_key and pre_key:
                            items.append(PreKeyItemType(device_id=device.id, registration_id=device.registration_id,
                                                        signed_pre_key=signed_key, pre_key=pre_key))
                            pre_key.delete()

                if items.__len__() > 0:
                    return PreKeyResponseType(identity_key=user.identity_key, devices=items)
        return None
