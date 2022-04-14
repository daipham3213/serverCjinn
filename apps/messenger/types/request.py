import graphene
from graphene_django import DjangoObjectType

from apps.account.models import User
from apps.messenger.models import Thread, MemberInfo


class AddFriendRequestType(graphene.ObjectType):
    to = graphene.String()


class FriendRequestType(graphene.ObjectType):
    class Meta:
        interfaces = (graphene.relay.Node,)

    pk = graphene.UUID()
    first_name = graphene.String()
    last_name = graphene.String()
    avatar = graphene.String()
    type = graphene.String()
    timestamp = graphene.DateTime()


class FriendRequestConnection(graphene.Connection):
    class Meta:
        node = FriendRequestType


class UserViewType(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        fields = ['id', 'first_name', 'last_name', 'avatar', 'dob', 'username', 'gender', 'date_joined']

    pk = graphene.UUID()

    def resolve_pk(self, info):
        return self.pk


class UserViewConnection(graphene.Connection):
    class Meta:
        node = UserViewType


class MemberViewType(DjangoObjectType):
    class Meta:
        model = MemberInfo
        exclude = ['thread', 'user_info']

    pk = graphene.UUID()
    info = graphene.Field(UserViewType)

    def resolve_pk(self, info, **kwargs):
        return self.pk

    def resolve_info(self, info, **kwargs):
        return User.objects.get(id=self.user_info.user_id)


class ThreadType(DjangoObjectType):
    class Meta:
        model = Thread
        interfaces = (graphene.relay.Node,)
        fields = ['id', 'name', 'icon', 'is_encrypted', 'extras', 'date_created', 'members']

    pk = graphene.UUID()
    leader = graphene.Field(UserViewType)
    members = graphene.List(MemberViewType)

    def resolve_leader(self, info, **kwargs):
        return User.objects.get(id=self.leader_id)

    def resolve_pk(self, info, **kwargs):
        return self.pk

    def resolve_members(self, info, **kwargs):
        return MemberInfo.objects.filter(thread_id=self.pk)


class ThreadTypeConnections(graphene.Connection):
    class Meta:
        node = ThreadType
