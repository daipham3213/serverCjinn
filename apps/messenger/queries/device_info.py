import graphene
from graphene_django import DjangoObjectType

from apps.messenger.models import DeviceInfo, PreKey, SignedPreKey


class DeviceInfoType(graphene.ObjectType):
    class Meta:
        model = DeviceInfo
        interfaces = (graphene.relay.Node,)
        fields = '__all__'


class DeviceInfoConnection(graphene.relay.Connection):
    class Meta:
        node = DeviceInfoType


class PreKeyQLType(DjangoObjectType):
    class Meta:
        model = PreKey
        fields = '__all__'


class SignedPreKeyType(DjangoObjectType):
    class Meta:
        model = SignedPreKey
        fields = '__all__'


class PreKeyItemType(graphene.ObjectType):
    device_id = graphene.String()
    registration_id = graphene.String()
    signed_pre_key = graphene.Field(SignedPreKeyType)
    pre_key = graphene.Field(PreKeyQLType)


class PreKeyResponseType(graphene.ObjectType):
    identity_key = graphene.String()
    devices = graphene.List(PreKeyItemType)


class DeviceInfoQuery(graphene.ObjectType):
    get_all_device = graphene.relay.ConnectionField(DeviceInfoConnection)
    get_device_keys = graphene.Field(PreKeyResponseType, device_id=graphene.String())

    @staticmethod
    def resolve_get_all_device(root, info, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            return DeviceInfo.objects.filter(user=user)
        return None

    @staticmethod
    def resolve_get_all_device_keys(root, info, device_id, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            devices = DeviceInfo.objects.filter(user=user)
            items = []
            if devices.count() > 0:
                for device in devices:
                    if device.is_enabled() and (device_id == '*' or device_id == device.id):
                        signed_key = device.signed_pre_key
                        pre_key = device.prekey_set.latest()
                        if signed_key and pre_key:
                            items.append(PreKeyItemType(device_id=device.id, registration_id=device.registration_id,
                                                        signed_pre_key=signed_key, pre_key=pre_key))
                if items.__len__() > 0:
                    return PreKeyResponseType(identity_key=user.identity_key, devices=items)
        return None
