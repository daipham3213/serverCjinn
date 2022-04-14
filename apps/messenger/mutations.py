import graphene
from django.conf import settings
from graphene_file_upload.scalars import Upload

from apps.base.converter import AutoCamelCasedScalar
from apps.base.mixins import DynamicArgsMixin, MutationMixin
from apps.messenger.mixins import AddSignedPreKeyMixin, AddKeyBundleMixin, CreateDeviceTokenMixin, \
    VerifyDeviceTokenMixin, RemoveDeviceMixin, SendMessageMixin, AddThreadMixin, UpdateDeviceInfoMixin, \
    SendFriendRequestMixin, ProcessFriendRequestMixin, RemoveContactMixin, SeenMessageMixin, UpdateAccountInfoMixin, \
    CallSignaling2Mixin
from apps.messenger.mixins.message_delivery import CallSignalingMixin


class PreKeyInput(graphene.InputObjectType):
    key_id = graphene.String(required=True)
    public_key = graphene.String(required=True)


class SignedPreKeyInput(graphene.InputObjectType):
    key_id = graphene.String(required=True)
    public_key = graphene.String(required=True)
    signature = graphene.String(required=True)


class MessageInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    destination_device_id = graphene.UUID(required=True)
    thread_id = graphene.UUID(required=True)
    contents = graphene.String(required=True)
    reply_to = graphene.UUID()
    extras = graphene.JSONString()
    # member_id or user_id?  current is member_id
    created_by = graphene.UUID(required=True)


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


class UpdateDeviceInfo(MutationMixin, UpdateDeviceInfoMixin, DynamicArgsMixin, graphene.Mutation):
    __doc__ = UpdateDeviceInfoMixin.__doc__

    result = AutoCamelCasedScalar()

    _args = ['gcm_id', 'apn_id', 'void_apn_id']


class RemoveDevice(MutationMixin, DynamicArgsMixin, RemoveDeviceMixin, graphene.Mutation):
    __doc__ = RemoveDeviceMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['registration_id']


class SendMessage(MutationMixin, SendMessageMixin, graphene.Mutation):
    __doc__ = SendMessageMixin.__doc__

    result = AutoCamelCasedScalar()

    class Arguments:
        files = graphene.List(Upload)
        messages = graphene.List(MessageInput, required=True)


class AddThread(MutationMixin, DynamicArgsMixin, AddThreadMixin, graphene.Mutation):
    __doc__ = AddThreadMixin.__doc__

    result = AutoCamelCasedScalar()

    # _required_args = ['name', 'member_ids', 'is_encrypt']

    class Arguments:
        name = graphene.String()
        member_ids = graphene.List(graphene.UUID, required=True)
        is_encrypt = graphene.Boolean(required=True)


class SendFriendRequest(MutationMixin, DynamicArgsMixin, SendFriendRequestMixin, graphene.Mutation):
    __doc__ = SendFriendRequestMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['recipient_id']


class ProcessFriendRequest(MutationMixin, DynamicArgsMixin, ProcessFriendRequestMixin, graphene.Mutation):
    __doc__ = ProcessFriendRequestMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['sender_id', 'is_accept']


class RemoveContact(MutationMixin, DynamicArgsMixin, RemoveContactMixin, graphene.Mutation):
    __doc__ = RemoveContactMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['user_id']


class SeenMessages(MutationMixin, DynamicArgsMixin, SeenMessageMixin, graphene.Mutation):
    __doc__ = SeenMessageMixin.__doc__

    result = AutoCamelCasedScalar()

    class Arguments:
        thread_id = graphene.UUID(required=True)
        message_ids = graphene.List(graphene.UUID, required=True)


class UpdateUserInfo(MutationMixin, UpdateAccountInfoMixin, graphene.Mutation):
    __doc__ = UpdateAccountInfoMixin.__doc__

    result = AutoCamelCasedScalar()

    class Arguments:
        phone = graphene.String()
        fist_name = graphene.String()
        last_name = graphene.String()
        dob = graphene.Date()
        language = graphene.Enum('LANG', [('vi', 'vi'), ('en', 'en')])()
        gender = graphene.Enum('GENDER', [('male', 'male'), ('female', 'female')])()
        discoverable_by_phone_number = graphene.Boolean()


class CallSignaling(MutationMixin, CallSignalingMixin, graphene.Mutation):
    __doc__ = CallSignalingMixin.__doc__

    result = AutoCamelCasedScalar()
    class Arguments:
        user_id = graphene.UUID()
        signal_type = graphene.String(required=True)
        has_video = graphene.Boolean()
        meeting_id = graphene.UUID()


# signal type, has_video, call_id, recipients, answer, offer
# class CallSignaling(MutationMixin, CallSignaling2Mixin, graphene.Mutation):
#     __doc__ = CallSignaling2Mixin.__doc__

#     result = AutoCamelCasedScalar()

#     class Arguments:
#         signal_type = graphene.String(required=True)
#         has_video = graphene.Boolean()
#         call_id = graphene.UUID()
#         to = graphene.UUID()
#         answer = AutoCamelCasedScalar()
#         offer = AutoCamelCasedScalar()
#         offer_candidate = AutoCamelCasedScalar()
#         answer_candidate = AutoCamelCasedScalar()
