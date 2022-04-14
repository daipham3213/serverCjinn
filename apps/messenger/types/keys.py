import graphene
from graphene_django import DjangoObjectType

from apps.messenger.models import PreKey, SignedPreKey


class PreKeyType(graphene.ObjectType):
    id = graphene.Int()
    public_key = graphene.String()

class SignedPreKeyType(DjangoObjectType):
    class Meta:
        model = SignedPreKey
        fields = ['id', 'public_key', 'signature']


class PreKeyCount(graphene.ObjectType):
    count = graphene.Int()


class PreKeyItemType(graphene.ObjectType):
    device_id = graphene.String()
    registration_id = graphene.Int()
    signed_pre_key = graphene.Field(SignedPreKeyType)
    pre_key = graphene.Field(PreKeyType)


class PreKeyResponseType(graphene.ObjectType):
    identity_key = graphene.String()
    devices = graphene.List(PreKeyItemType)
