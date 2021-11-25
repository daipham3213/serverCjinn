import graphene
from graphene_django.debug import DjangoDebug

from .converter import FieldsPatches

# Converters - Must be put above other schema imports!!

FieldsPatches()

# Schemas
from apps.log.schema import LogQuery
from apps.account.schema import AccountMutation, UserQuery
from ..messenger.schema import MessengerMutation, MessengerQuery, MessengerSubscriptions


class Subscription(MessengerSubscriptions, graphene.ObjectType):
    # messenger = graphene.Field(MessengerSubscriptions)
    pass


class Mutation(graphene.ObjectType):
    messenger = graphene.Field(MessengerMutation)
    account = graphene.Field(AccountMutation)

    @staticmethod
    def resolve_account(root: None, info: graphene.ResolveInfo):
        return AccountMutation()

    @staticmethod
    def resolve_messenger(root: None, info: graphene.ResolveInfo):
        return MessengerMutation()


class Query(graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='__debug')
    user = graphene.Field(UserQuery)
    logs = graphene.Field(LogQuery)
    messenger = graphene.Field(MessengerQuery)

    @staticmethod
    def resolve_messenger(root: None, info: graphene.ResolveInfo):
        return MessengerQuery()

    @staticmethod
    def resolve_logs(root: None, info: graphene.ResolveInfo):
        if hasattr(info.context, 'user') and info.context.user.is_superuser:
            return LogQuery()

    @staticmethod
    def resolve_user(root: None, info: graphene.ResolveInfo):
        return UserQuery()


schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)
