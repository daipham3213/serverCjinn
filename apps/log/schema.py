import graphene

from apps.log.models import ActivityLog, HistoryLog, AuthorizationLog
from apps.log.types import ActivityLogNode, HistoryLogNode, AuthorizationLogNode


class ActivityConnection(graphene.relay.Connection):
    class Meta:
        node = ActivityLogNode


class HistoryLogConnection(graphene.relay.Connection):
    class Meta:
        node = HistoryLogNode


class AuthorizeLogConnection(graphene.relay.Connection):
    class Meta:
        node = AuthorizationLogNode


class LogQuery(graphene.ObjectType):
    activities = graphene.relay.ConnectionField(ActivityConnection)
    histories = graphene.relay.ConnectionField(HistoryLogConnection)
    authorize = graphene.relay.ConnectionField(AuthorizeLogConnection)

    @staticmethod
    def resolve_activities(root, info, **kwargs):
        return ActivityLog.objects.all()

    @staticmethod
    def resolve_histories(root, info, **kwargs):
        return HistoryLog.objects.all()

    @staticmethod
    def resolve_authorize(root, info, **kwargs):
        result = AuthorizationLog.objects.all()
        return result

