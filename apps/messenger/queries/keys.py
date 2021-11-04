import graphene
from graphene_django import DjangoObjectType

from apps.messenger.models import PreKey


class PreKeyType(DjangoObjectType):
    class Meta:
        model = PreKey
        fields = ('',)


class PreKeyCount(graphene.ObjectType):
    count = graphene.Int()


class KeyQuery(graphene.ObjectType):
    get_status = graphene.Field(PreKeyCount, device_id=graphene.String())
    get_device_keys = graphene.Field()

    @staticmethod
    def resolve_get_status(root, info, device_id, **kwargs):
        if hasattr(info.context, 'user'):
            user = info.context.user
            return PreKey.objects.filter(user=user, device_id=device_id).count()
        return None
