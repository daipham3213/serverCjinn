import graphene

from apps.messenger.models import DeviceInfo


class DeviceInfoType(graphene.ObjectType):
    class Meta:
        model = DeviceInfo
        interfaces = (graphene.relay.Node,)
        fields = '__all__'


class DeviceInfoConnection(graphene.relay.Connection):
    class Meta:
        node = DeviceInfoType
