import graphene

from apps.messenger.func import get_user_cache
from apps.messenger.models import UserInfo
from apps.messenger.types import FriendOnlineType


class MessageQuery(graphene.ObjectType):
    friends_online = graphene.List(FriendOnlineType)

    @staticmethod
    def resolve_friends_online(root, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            arr = []
            user_info = UserInfo.objects.get(user_id=user.id)
            if user_info:
                contacts = user_info.contacts.split('|')
                for user_id in contacts:
                    friend = get_user_cache(user_id)
                    if friend:
                        arr.append(FriendOnlineType(user_id=user_id, status='online'))
            return arr
        return None
