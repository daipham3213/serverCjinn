import graphene

from apps.base.converter import AutoCamelCasedScalar
from apps.base.mixins import DynamicArgsMixin, MutationMixin
from apps.messenger.mixins import AddSignedPreKeyMixin, AddKeyBundleMixin, CreateDeviceTokenMixin, \
    VerifyDeviceTokenMixin, RemoveDeviceMixin


class PreKeyInput(graphene.InputObjectType):
    key_id = graphene.String(required=True)
    public_key = graphene.String(required=True)


class SignedPreKeyInput(graphene.InputObjectType):
    key_id = graphene.String(required=True)
    public_key = graphene.String(required=True)
    signature = graphene.String(required=True)


class AddSignedPreKey(MutationMixin, DynamicArgsMixin, AddSignedPreKeyMixin, graphene.Mutation):
    __doc__ = AddSignedPreKeyMixin.__doc__

    result = AutoCamelCasedScalar()
    _required_args = ['registrationId']


class AddKeyBundle(MutationMixin, AddKeyBundleMixin, graphene.Mutation):
    __doc__ = AddKeyBundleMixin.__doc__

    result = AutoCamelCasedScalar()

    class Arguments:
        pre_keys = graphene.List(PreKeyInput)
        signed_pre_key = SignedPreKeyInput(required=True)
        identity_key = graphene.String(required=True)
        registration_id = graphene.String(required=True)


class CreateDeviceToken(MutationMixin, CreateDeviceTokenMixin, DynamicArgsMixin, graphene.Mutation):
    __doc__ = CreateDeviceTokenMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['registrationId']


class VerifyDeviceToken(MutationMixin, VerifyDeviceTokenMixin, DynamicArgsMixin, graphene.Mutation):
    __doc__ = VerifyDeviceTokenMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['password', 'registrationId', 'otp', 'deviceName']


class RemoveDevice(MutationMixin, DynamicArgsMixin, RemoveDeviceMixin, graphene.Mutation):
    __doc__ = RemoveDeviceMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['deviceId']
