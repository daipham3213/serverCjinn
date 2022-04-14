import graphene
from graphene_django import DjangoObjectType

from apps.messenger.models import DeviceInfo


class DeviceInfoType(DjangoObjectType):
    class Meta:
        model = DeviceInfo
        interfaces = (graphene.relay.Node,)
        fields = '__all__'


class DeviceInfoConnection(graphene.relay.Connection):
    class Meta:
        node = DeviceInfoType


class DeviceInfoView(DjangoObjectType):
    class Meta:
        model = DeviceInfo
        fields = ['id', 'registration_id', 'last_seen']

    pk = graphene.UUID()

    def resolve_pk(self, info):
        return self.pk
