import graphene
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from graphene_django import DjangoObjectType

from apps.account.models import RoleGroup
from apps.messenger.func import get_user_cache
from apps.messenger.models import UserInfo

UserModel = get_user_model()


class RoleGroupNode(DjangoObjectType):
    class Meta:
        model = RoleGroup
        fields = ('id', 'name', 'user_created', 'date_created', 'date_modified')
        filter_fields = ['name', 'user_created', ]


class UserNode(DjangoObjectType):
    class Meta:
        model = UserModel
        interfaces = (graphene.relay.Node,)
        skip_registry = True
        fields = (
            'id', 'first_name', 'last_name', 'username', 'email', 'phone', 'dob', 'gender',
            'language', 'avatar', 'is_email', 'is_phone', 'date_joined', 'is_active')
        filter_fields = ['first_name', 'last_name', 'username', 'email', 'phone', ]

    pk = graphene.UUID()

    def resolve_pk(self, info):
        return self.pk

    @classmethod
    def get_queryset(cls, queryset: QuerySet, info):
        return queryset.filter(discoverable_by_phone_number=True)


class UserInfoType(DjangoObjectType):
    class Meta:
        model = UserModel
        fields = (
            'first_name', 'last_name', 'username', 'email', 'phone', 'dob', 'gender',
            'language', 'avatar', 'is_email', 'is_phone', 'date_joined', 'is_active'
        )

    pk = graphene.UUID()
    status = graphene.String()
    contact_status = graphene.String()

    # status = graphene.Enum('online_status', [('online', 1), ('offline', 0)])
    # contact_status = graphene.Enum('contact_status',
    #                                [('waiting', 0), ('requested', 1), ('in_contact', 2), ('no_contact', 3)])

    def resolve_pk(self, info):
        return self.pk

    def resolve_status(self, info):
        user = get_user_cache(user_id=self.pk)
        if user and user.devices:
            for device in user.devices:
                if device.friend_online:
                    return 'online'
        return 'offline'

    def resolve_contact_status(self, info, **kwargs):
        user_info = UserInfo.objects.filter(user_id=self.pk).first()
        if user_info.contacts and user_info.contacts.__contains__(info.context.user.id.__str__()):
            return 'in_contact'
        requests = user_info.get_friend_requests()
        if requests:
            req = requests.get(info.context.user.id.__str__(), None)
            if req and req.get('type') == 'sender':
                return 'waiting'
            elif req and req.get('type') == 'receiver':
                return 'requested'
        return 'no_contact'


class MeNode(DjangoObjectType):
    class Meta:
        model = UserModel
        interfaces = (graphene.relay.Node,)
        skip_registry = True
        fields = (
            'id', 'first_name', 'last_name', 'username', 'email', 'phone', 'dob', 'gender',
            'language', 'avatar', 'is_email', 'is_phone', 'date_joined', 'is_active')
        filter_fields = ['first_name', 'last_name', 'username', 'email', 'phone', ]

    pk = graphene.UUID()

    def resolve_pk(self, info):
        return self.pk
