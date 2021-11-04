import graphene

from apps.messenger.mutations import AddSignedPreKey, AddKeyBundle, CreateDeviceToken, VerifyDeviceToken, RemoveDevice
from apps.messenger.queries.device_info import DeviceInfoQuery


class MessengerMutation(graphene.ObjectType):
    add_signed_pre_key = AddSignedPreKey.Field()
    add_key_bundles = AddKeyBundle.Field()
    create_device_token = CreateDeviceToken.Field()
    verify_device_token = VerifyDeviceToken.Field()
    remove_device = RemoveDevice.Field()


class MessengerQuery(graphene.ObjectType):
    device = graphene.Field(DeviceInfoQuery)
    