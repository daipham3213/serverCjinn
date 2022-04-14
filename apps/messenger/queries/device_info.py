import graphene

from apps.messenger.models import DeviceInfo
from apps.messenger.types.credentials import DeviceInfoConnection, DeviceInfoView, DeviceInfoType


class DeviceInfoQuery(graphene.ObjectType):
    get_all_device = graphene.relay.ConnectionField(DeviceInfoConnection)
    get_current_device = graphene.Field(DeviceInfoType)
    get_device_by_user_id = graphene.List(DeviceInfoView, user_id=graphene.UUID())

    @staticmethod
    def resolve_get_all_device(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            user = info.context.user
            return DeviceInfo.objects.filter(user=user)

    @staticmethod
    def resolve_get_current_device(root, info, **kwargs):
        if hasattr(info.context, 'device'):
            return info.context.device

    @staticmethod
    def resolve_get_device_by_user_id(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            devices = DeviceInfo.objects.filter(user_id=kwargs.get('user_id'))
            return devices
