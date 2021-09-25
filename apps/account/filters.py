from django_filters import rest_framework as filters

from apps.base.middleware import get_user_extra
from apps.base.utils import check_uuid


class PermissionListByUserFilter(filters.FilterSet):
    user = filters.UUIDFilter()
    application = filters.CharFilter()
    model = filters.CharFilter()
    codename = filters.CharFilter()
    doc_id = filters.UUIDFilter()

    @classmethod
    def validate(cls, data):
        if 'user' in data:
            if not check_uuid(data['user']):
                return False
            else:
                user_org = get_user_extra()
                if str(data['user']) != str(user_org['user'].id):
                    return False
        if 'application' in data:
            if not isinstance(data['application'], str):
                return False
        if 'model' in data:
            if not isinstance(data['model'], str):
                return False
        if 'codename' in data:
            if not isinstance(data['codename'], str):
                return False
        if 'doc_id' in data:
            if not check_uuid(data['doc_id']):
                return False
        return True

