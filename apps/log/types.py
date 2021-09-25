import graphene

from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType

from apps.account.types import UserNode
from apps.log.filters import ActivityLogListFilter, HistoryLogListFilter
from apps.log.models import ActivityLog, HistoryLog, AuthorizationLog, DocumentLog

UserModel = get_user_model()


class ActivityLogNode(DjangoObjectType):
    user_created = graphene.Field(UserNode)

    class Meta:
        model = ActivityLog
        interfaces = (graphene.relay.Node,)
        filterset_class = ActivityLogListFilter
        fields = (
            'id', 'date_created', 'date_modified', 'user_created', 'remarks', 'data', 'doc_id', 'doc_name', 'node_id',
            'node_name', 'node_type', 'reason', 'code_document', 'is_active')

    def resolve_user_created(self, info):
        user_created = UserModel.objects.get(pk=self.user_created)
        return user_created


class HistoryLogNode(DjangoObjectType):
    class Meta:
        model = HistoryLog
        interfaces = (graphene.relay.Node,)
        filterset_class = HistoryLogListFilter
        fields = (
            'id', 'date_created', 'user_created', 'remarks', 'code_document', 'doc_id', 'doc_name', 'doc_detail',
            'doc_new',
            'doc_change', 'activity_name', 'is_active')


class AuthorizationLogNode(DjangoObjectType):
    class Meta:
        model = AuthorizationLog
        interfaces = (graphene.relay.Node,)
        fields = ('id', 'date_created', 'date_modified', 'user_created', 'remarks', 'data', 'is_active')


class DocumentLogNode(DjangoObjectType):
    class Meta:
        model = DocumentLog
        interfaces = (graphene.relay.Node,)
        fields = (
            'id', 'user_created', 'employee_inherit', 'code_document', 'doc_id', 'doc_name', 'doc_code', 'doc_status',
            'date_created', 'date_modified', 'is_active')
