from django_filters import rest_framework as filters

from apps.base.utils import check_uuid
from apps.log.models import ActivityLog, HistoryLog


class ActivityLogListFilter(filters.FilterSet):
    doc_id = filters.CharFilter(method='filter_doc_id')
    user_created = filters.CharFilter(method='filter_user_created')

    def filter_doc_id(self, queryset, key, value):
        if value == 'none' or value == 'null':
            return queryset.filter(**{key + '__isnull': True})
        elif check_uuid(value):
            return queryset.filter(**{key: value})
        return ActivityLog.objects.none()

    def filter_user_created(self, queryset, key, value):
        if value == 'none' or value == 'null':
            return queryset.filter(**{key + '__isnull': True})
        elif check_uuid(value):
            return queryset.filter(**{key: value})
        return ActivityLog.objects.none()

    class Meta:
        model = ActivityLog
        fields = ('doc_id', 'user_created')


class HistoryLogListFilter(filters.FilterSet):
    doc_id = filters.CharFilter(method='filter_doc_id')
    user_created = filters.CharFilter(method='filter_user_created')

    def filter_doc_id(self, queryset, key, value):
        if value == 'none' or value == 'null':
            return queryset.filter(**{key + '__isnull': True})
        elif check_uuid(value):
            return queryset.filter(**{key: value})
        return ActivityLog.objects.none()

    def filter_user_created(self, queryset, key, value):
        if value == 'none' or value == 'null':
            return queryset.filter(**{key + '__isnull': True})
        elif check_uuid(value):
            return queryset.filter(**{key: value})
        return ActivityLog.objects.none()

    class Meta:
        model = HistoryLog
        fields = ('doc_id', 'user_created')
