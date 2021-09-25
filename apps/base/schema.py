import graphene
from graphene_django.debug import DjangoDebug
from .converter import FieldsPatches

# Converters - Must be put above other schema imports!!
FieldsPatches()

# Schemas
from apps.log.schema import LogQuery
from apps.account.schema import AccountMutation, UserQuery, MeQuery


class Mutation(AccountMutation, graphene.ObjectType):
    pass


class Query(LogQuery, UserQuery, MeQuery, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='__debug')
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
