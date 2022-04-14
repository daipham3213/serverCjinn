import graphene

from apps.messenger.mutations import AddSignedPreKey, AddKeyBundle, CreateDeviceToken, VerifyDeviceToken, RemoveDevice, \
    AddThread, SendMessage, UpdateDeviceInfo, SendFriendRequest, ProcessFriendRequest, RemoveContact, SeenMessages, \
    UpdateUserInfo, CallSignaling
from apps.messenger.queries import DeviceInfoQuery, KeyQuery, MessageQuery
from apps.messenger.subscriptions import MessengerSubscription, FriendOnlineSubscription, \
    FriendRequestSubscription, PrivateChannelSubscription, CallSignalingSubscription


class MessengerMutation(graphene.ObjectType):
    add_signed_pre_key = AddSignedPreKey.Field()
    add_key_bundles = AddKeyBundle.Field()
    create_device_token = CreateDeviceToken.Field()
    update_device_info = UpdateDeviceInfo.Field()
    verify_device_token = VerifyDeviceToken.Field()
    remove_device = RemoveDevice.Field()
    add_thread = AddThread.Field()
    send_message = SendMessage.Field()
    send_friend_request = SendFriendRequest.Field()
    process_friend_request = ProcessFriendRequest.Field()
    remove_contact = RemoveContact.Field()
    seen_signal = SeenMessages.Field()
    update_user_info = UpdateUserInfo.Field()
    call_signaling = CallSignaling.Field()


class MessengerQuery(DeviceInfoQuery, KeyQuery, MessageQuery, graphene.ObjectType):
    pass


class MessengerSubscriptions(graphene.ObjectType):
    friend_online = FriendOnlineSubscription.Field()
    incoming_message = MessengerSubscription.Field()
    friend_request = FriendRequestSubscription.Field()
    private_channel = PrivateChannelSubscription.Field()
    call_signaling = CallSignalingSubscription.Field()
