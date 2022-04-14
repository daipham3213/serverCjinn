import graphene
from datetime import datetime
from django.db.models import Q

from apps.account.models import User
from apps.messenger.func import get_user_cache
from apps.messenger.models import UserInfo, Thread
from apps.messenger.models.redis import Calls
from apps.messenger.types import FriendRequestConnection, FriendOnlineConnection, ThreadTypeConnections, \
    UserViewConnection, FriendOnlineType, FriendRequestType, ThreadType, MeetingType


class MessageQuery(graphene.ObjectType):
    friends_online = graphene.relay.ConnectionField(FriendOnlineConnection)
    friend_request = graphene.relay.ConnectionField(FriendRequestConnection)
    thread_list = graphene.relay.ConnectionField(ThreadTypeConnections, ids=graphene.List(graphene.UUID, required=True))
    thread = graphene.Field(ThreadType, id=graphene.UUID(required=True))
    thread_by_user_ids = graphene.Field(ThreadType, user_ids=graphene.List(graphene.UUID, required=True))
    contacts = graphene.relay.ConnectionField(UserViewConnection)
    search_contacts = graphene.relay.ConnectionField(UserViewConnection, keyword=graphene.String())
    get_online_status = graphene.Field(FriendOnlineType, user_id=graphene.UUID(required=True))
    get_meeting = graphene.Field(MeetingType, meeting_id=graphene.UUID(required=True))

    @staticmethod
    def resolve_get_online_status(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            user_info = UserInfo.objects.get(user=info.context.user)
            contacts = user_info.get_contacts()
            friend_id = kwargs.get('user_id')
            if contacts.__contains__(friend_id):
                friend = get_user_cache(friend_id.__str__())
                if friend:
                    for d in friend.devices:
                        if d.friend_online:
                            return FriendOnlineType(user_id=friend_id, status='online')
                else:
                    return FriendOnlineType(user_id=friend_id, status='offline')

    @staticmethod
    def resolve_friends_online(root, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            arr = []
            user_info = UserInfo.objects.get(user_id=user.id)
            if user_info:
                contacts = user_info.get_contacts()
                for user_id in contacts:
                    friend = get_user_cache(user_id)
                    if friend:
                        for d in friend.devices:
                            if d.friend_online is True:
                                arr.append(FriendOnlineType(user_id=user_id, status='online'))
            return arr
        return []

    @staticmethod
    def resolve_friend_request(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            user = info.context.user
            user_info = UserInfo.objects.filter(user_id=user.id).first()
            requests = user_info.get_friend_requests()
            result = []
            for key, value in requests.items():
                sender = User.objects.get(id=key)
                if sender:
                    # 2021-12-27 21:34:53.160763
                    time = datetime.strptime(value['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
                    result.append(FriendRequestType(pk=sender.id, first_name=sender.first_name, last_name=sender.last_name, avatar=sender.avatar, timestamp=time, type=value['type']))
            return result
        return []

    @staticmethod
    def resolve_thread_list(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            user = info.context.user
            user_info = UserInfo.objects.filter(user_id=user.id).first()
            return user_info.threads.filter(id__in=kwargs.get('ids'))
        return []

    @staticmethod
    def resolve_contacts(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            user = info.context.user
            user_info = UserInfo.objects.filter(user_id=user.id).first()
            contacts = ' '.join(user_info.contacts.split('|')).split()
            return User.objects.filter(id__in=contacts)
        return []

    @staticmethod
    def resolve_search_contacts(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            user = info.context.user
            user_info = UserInfo.objects.filter(user_id=user.id).first()
            contacts = user_info.get_contacts()
            keyword = kwargs.get('keyword', None)
            if keyword:
                filter_set = Q(username__icontains=keyword) | Q(first_name__icontains=keyword) | Q(
                    last_name__icontains=keyword) | Q(email__icontains=keyword) | Q(phone__icontains=keyword)
                results = User.objects.filter(filter_set, id__in=contacts)
            else:
                results = User.objects.filter(id__in=contacts)
            return results
        return []

    @staticmethod
    def resolve_thread(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            user = info.context.user
            user_info = UserInfo.objects.filter(user_id=user.id).first()
            try:
                return Thread.objects.filter(memberinfo__user_info=user_info, id=kwargs.get('id')).first()
            except ValueError:
                pass

    @staticmethod
    def resolve_thread_by_user_ids(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            try:
                user_ids = kwargs.get('user_ids')
                return Thread.get_thread_by_list_user(user_ids).first()
            except Thread.DoesNotExist:
                pass

    @staticmethod
    def resolve_get_meeting(root, info, meeting_id):
        call = Calls.get_call(meeting_id)
        return MeetingType(pk=meeting_id, offers=call.offers, answers=call.answers, members=call.members,
                           has_video=call.has_video) if call else None
