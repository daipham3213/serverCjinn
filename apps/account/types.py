import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType

from apps.account.models import RoleGroup

UserModel = get_user_model()


class RoleGroupNode(DjangoObjectType):
    class Meta:
        model = RoleGroup
        fields = ('id', 'name', 'user_created', 'date_created', 'date_modified')
        filter_fields = ['name', 'user_created', ]


class UserNode(DjangoObjectType):
    groups = graphene.Field(RoleGroupNode)

    class Meta:
        model = UserModel
        interfaces = (graphene.relay.Node,)
        skip_registry = True
        fields = (
            'id', 'first_name', 'last_name', 'username', 'email', 'phone', 'dob', 'gender', 'groups', 'permissions',
            'language', 'avatar', 'is_email', 'is_phone', 'date_joined', 'is_active')
        filter_fields = ['first_name', 'last_name', 'username', 'email', 'phone', ]

    pk = graphene.Int()

    def resolve_pk(self, info):
        return self.pk
