from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Q

from .models import RoleGroup, UserPermission, GroupPermission, UserRoleGroup

# permission
from ..base.middleware import get_user_extra
from ..base.utils import check_uuid


def format_codename_to_all(code_name):
    if code_name.startswith('view') and '_all_' not in code_name:
        return code_name.replace('view', 'view_all', 1)
    elif code_name.startswith('change') and '_all_' not in code_name:
        return code_name.replace('change', 'change_all', 1)
    elif code_name.startswith('delete') and '_all_' not in code_name:
        return code_name.replace('delete', 'delete_all', 1)
    return code_name


def get_identity(identity):
    if isinstance(identity, get_user_model()):
        return identity, None
    if isinstance(identity, RoleGroup):
        return None, identity
    raise ValueError('User or RoleGroup instance is required "(got %s)"' % identity)


# ----------> end new version permission
def list_perm(user_or_group, application=None, doc_id=None, doc_type=None, model=None, codename=None):
    user, group = get_identity(user_or_group)

    kwargs = {}

    if application:
        kwargs.update({'permission__content_type__app_label': application})
    if doc_id:
        kwargs.update({'doc_id': doc_id})
    else:
        kwargs.update({'doc_id__isnull': True})
    if doc_type:
        kwargs.update({'doc_type': doc_type})
    if model:
        kwargs.update({"permission__content_type__model": model})
    if codename:
        kwargs.update({"permission__codename": codename})

    if user:
        list_permissions = []
        code_perm_account_user = []

        # filter permission admin
        filter_content_id = Q()
        for admin_granted in settings.PERMISSION_ADMIN_FAVOR:
            filter_content_id.add(Q(app_label=admin_granted['app_label'], model=admin_granted['model']), Q.OR)
        content_type_account_user = ContentType.objects.filter(app_label='account', model='user').values_list('id',
                                                                                                              flat=True)

        kwargs.update({'user_id': user.id})
        user_perms = UserPermission.objects.select_related('permission').filter(**kwargs).annotate(
            content_type_id=F('permission__content_type_id'), name=F('permission__name'),
            codename=F('permission__codename')
        ).values('name', 'codename', 'content_type_id', 'option', 'more', 'lower_level').distinct()
        for perm in user_perms:
            code_perm_account_user.append(perm['codename']) if perm[
                                                                   'content_type_id'] in content_type_account_user else None
            list_permissions.append({
                'name': perm['name'], 'codename': perm['codename'], 'option': perm['option'],
                'more': perm['more'], 'lower_level': perm['lower_level']
            })
        if user.is_superuser or user.is_staff:
            admin_filter = Q()
            if application is None and model is None:
                if doc_id is None and codename is None:
                    [
                        admin_filter.add(
                            Q(content_type__app_label=admin_granted['app_label'],
                              content_type__model=admin_granted['model']), Q.OR
                        ) for admin_granted in settings.PERMISSION_ADMIN_FAVOR
                    ]
                elif codename is not None:
                    admin_filter.add(
                        Q(
                            codename=codename,
                            content_type__app_label__in=[x['app_label'] for x in settings.PERMISSION_ADMIN_FAVOR],
                            content_type__model__in=[x['model'] for x in settings.PERMISSION_ADMIN_FAVOR]
                        ), Q.OR
                    )
            else:
                for admin_granted in settings.PERMISSION_ADMIN_FAVOR:
                    if application == admin_granted['app_label']:
                        if model is None:
                            admin_filter.add(Q(content_type__app_label=admin_granted['app_label'],
                                               content_type__model=admin_granted['model']), Q.OR)
                        elif model == admin_granted['model']:
                            admin_filter.add(Q(content_type__app_label=admin_granted['app_label'],
                                               content_type__model=admin_granted['model']), Q.OR)

            # admin permission have been granted
            if admin_filter:
                admin_permissions = Permission.objects.filter(admin_filter)
                for perm in admin_permissions:
                    if perm.codename not in code_perm_account_user:
                        list_permissions.append(
                            {'name': perm.name, 'codename': perm.codename, 'option': 1 if user.is_superuser else 2, 'more': [],
                             'lower_level': False})

        return list_permissions

    if group:
        kwargs.update({'group_id': group.id})
        group_perms = GroupPermission.objects.select_related('permission').filter(**kwargs).annotate(
            name=F('permission__name'), codename=F('permission__codename')
        ).values('name', 'codename', 'option', 'more', 'lower_level')
        for perm in group_perms:
            perm.update({
                'option': perm.get('option', None),
                'more': perm.get('more', None),
                'lower_level': perm.get('lower_level', None)
            })
        return group_perms if group_perms else []

    return []


def user_permissions(user, application_code=None, doc_id=None, model=None, codename=None):
    if not isinstance(user, get_user_model()):
        if not check_uuid(user, 4):
            return []
        else:
            try:
                user = get_user_model().objects.get(pk=user)
            except Exception as e:
                print(e)
                return []
    results = []
    user_org = get_user_extra()
    org_user = user_org.get('user')
    if org_user:
        results += list_perm(user, application=application_code, doc_id=doc_id, model=model, codename=codename)
        for group in user.groups.all():
            results += list_perm(group, application=application_code, doc_id=doc_id, model=model, codename=codename)
    return results
