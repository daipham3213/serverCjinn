import graphene

from apps.log.types import ActivityLogNode, HistoryLogNode, AuthorizationLogNode
from graphene_django.filter.fields import DjangoFilterConnectionField


class LogQuery(graphene.ObjectType):
    activities = graphene.List(ActivityLogNode)
    histories = graphene.List(HistoryLogNode)
    authorize = graphene.List(AuthorizationLogNode)
