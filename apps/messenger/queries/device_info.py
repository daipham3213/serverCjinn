import graphene

from apps.messenger.models import DeviceInfo
from apps.messenger.types.credentials import DeviceInfoConnection


class DeviceInfoQuery(graphene.ObjectType):
    get_all_device = graphene.relay.ConnectionField(DeviceInfoConnection)
    get_current_device = graphene.Field(DeviceInfoConnection)
    get_device = graphene.Field(DeviceInfoConnection, registration_id=graphene.UUID())

    @staticmethod
    def resolve_get_all_device(root, info, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            return DeviceInfo.objects.filter(user=user)
        return None

    @staticmethod
    def resolve_get_current_device(root, info, **kwargs):
        if hasattr(info.context, 'device'):
            return info.context.device
        return None

    @staticmethod
    def resolve_get_device(root, info, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context
            return DeviceInfo.objects.filter(user=user, registration_id=kwargs.get('registration_id', None)).first()
        return None
