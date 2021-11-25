import graphene
from graphene_django import DjangoObjectType

from apps.messenger.models import PreKey, SignedPreKey


class PreKeyType(DjangoObjectType):
    class Meta:
        model = PreKey
        fields = '__all__'


class SignedPreKeyType(DjangoObjectType):
    class Meta:
        model = SignedPreKey
        fields = '__all__'


class PreKeyCount(graphene.ObjectType):
    count = graphene.Int()


class PreKeyItemType(graphene.ObjectType):
    device_id = graphene.String()
    registration_id = graphene.String()
    signed_pre_key = graphene.Field(SignedPreKeyType)
    pre_key = graphene.Field(PreKeyType)


class PreKeyResponseType(graphene.ObjectType):
    identity_key = graphene.String()
    devices = graphene.List(PreKeyItemType)
