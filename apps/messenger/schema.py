import graphene

from apps.messenger.mutations import AddSignedPreKey, AddKeyBundle, CreateDeviceToken, VerifyDeviceToken, RemoveDevice, \
    AddThread, SendMessage, UpdateDeviceInfo
from apps.messenger.queries import DeviceInfoQuery, KeyQuery
from apps.messenger.subscriptions import IncomingMessageSubscription, FriendOnlineSubscription, \
    FriendRequestSubscription


class MessengerMutation(graphene.ObjectType):
    add_signed_pre_key = AddSignedPreKey.Field()
    add_key_bundles = AddKeyBundle.Field()
    create_device_token = CreateDeviceToken.Field()
    update_device_info = UpdateDeviceInfo.Field()
    verify_device_token = VerifyDeviceToken.Field()
    remove_device = RemoveDevice.Field()
    add_thread = AddThread.Field()
    send_message = SendMessage.Field()


class MessengerQuery(graphene.ObjectType):
    device = graphene.Field(DeviceInfoQuery)
    key = graphene.Field(KeyQuery)

    @staticmethod
    def resolve_key(root: None, info: graphene.ResolveInfo):
        return KeyQuery()

    @staticmethod
    def resolve_device(root: None, info: graphene.ResolveInfo):
        return DeviceInfoQuery()


class MessengerSubscriptions(graphene.ObjectType):
    friend_online = FriendOnlineSubscription.Field()
    incoming_message = IncomingMessageSubscription.Field()
    friend_request = FriendRequestSubscription.Field()
